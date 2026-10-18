"""WarungScout D1 导出 → Brand OS 渠道点位导入器。

数据源（--src）支持两种：
- .json：Warung 行数组（D1 `wrangler d1 export --format json` 或 API 导出）
- .sqlite / .db：含 warungs 表的 SQLite 文件（D1 本地副本）

列映射对齐 warungscout/docs/DATABASE_SCHEMA.md 的 warungs 表：
    latitude/longitude → lat/lon；7 个 {dim}_score 直写 channel_points 同名列
    final_score / grade 缺失时回退 nbo.scoring 由 signals 计算（无历史 → 中性 50）
已灌入的点位可用 --replace 清空旧 warungscout 来源后重灌。
"""
import argparse
import json
import sqlite3
from pathlib import Path

from nbo.db import DB_PATH, migrate
from nbo.scoring import score_warung

DIM_COLS = ["location_score", "activity_score", "competition_score", "cooperation_score",
            "digital_score", "owner_score", "region_score"]

INSERT_SQL = ("INSERT OR REPLACE INTO channel_points VALUES "
              "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)")

VALID_GRADES = ("gold", "silver", "potential", "normal")


def load_rows(src: Path) -> list[dict]:
    if src.suffix.lower() == ".json":
        data = json.loads(src.read_text(encoding="utf-8"))
        if isinstance(data, dict):  # wrangler export 常见 {tables: {warungs: [...]}} 或 {warungs: [...]}
            data = data.get("warungs") or next(iter(data.get("tables", {}).values()), [])
        if not isinstance(data, list):
            raise ValueError("JSON 导出格式无法识别：期望 Warung 行数组")
        return data
    if src.suffix.lower() in (".sqlite", ".db", ".sqlite3"):
        conn = sqlite3.connect(src)
        conn.row_factory = sqlite3.Row
        try:
            return [dict(r) for r in conn.execute("SELECT * FROM warungs")]
        finally:
            conn.close()
    if src.suffix.lower() == ".sql":
        # wrangler d1 export 产物：CREATE TABLE + INSERT，灌进内存库再读
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        try:
            conn.executescript(src.read_text(encoding="utf-8"))
            return [dict(r) for r in conn.execute("SELECT * FROM warungs")]
        finally:
            conn.close()
    raise ValueError(f"不支持的数据源格式：{src.suffix}（仅 .json / .sqlite / .db / .sql）")


def map_row(row: dict) -> tuple | None:
    lat, lon = row.get("latitude"), row.get("longitude")
    if lat is None or lon is None:
        return None
    signals = row.get("signals") if isinstance(row.get("signals"), dict) else None
    dims = {c: row.get(c) for c in DIM_COLS}
    if any(v is None for v in dims.values()) or row.get("final_score") is None or row.get("grade") not in VALID_GRADES:
        r = score_warung({**(signals or {"no_history": True}), "city": row.get("city")})
        dims = {c: r["dims"][c.removesuffix("_score")] for c in DIM_COLS}
        final_score, grade = r["final_score"], r["grade"]
    else:
        final_score, grade = int(row["final_score"]), row["grade"]
    return (row.get("id"), row.get("name"), "warung", float(lat), float(lon),
            row.get("city"), row.get("region"), final_score, grade,
            int(row.get("sales_step") or 0), "warungscout",
            *dims.values(), json.dumps(signals, ensure_ascii=False) if signals else None)


def import_warungs(src: str | Path, db_path: str | Path = DB_PATH,
                   replace: bool = False) -> dict:
    src, db_path = Path(src), Path(db_path)
    migrate(db_path)
    rows = load_rows(src)
    conn = sqlite3.connect(db_path)
    n, skipped = 0, 0
    try:
        if replace:
            conn.execute("DELETE FROM channel_points WHERE source = 'warungscout'")
        for row in rows:
            m = map_row(row)
            if m is None:
                skipped += 1
                continue
            conn.execute(INSERT_SQL, m)
            n += 1
        conn.commit()
    finally:
        conn.close()
    return {"imported": n, "skipped_no_coords": skipped, "total_rows": len(rows)}


def main() -> None:
    ap = argparse.ArgumentParser(description="WarungScout D1 导出 → Brand OS 渠道点位")
    ap.add_argument("--src", required=True, help="D1 导出文件（.json 数组 或 .sqlite/.db）")
    ap.add_argument("--db", default=str(DB_PATH))
    ap.add_argument("--replace", action="store_true", help="先清空 source=warungscout 的旧点位")
    args = ap.parse_args()
    print(json.dumps(import_warungs(args.src, args.db, args.replace), ensure_ascii=False))


if __name__ == "__main__":
    main()
