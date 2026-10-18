"""数据导入管线：CSV -> JSON Schema 校验 -> SQLite。

Schema 为 data/schemas/*.json（draft-07 子集：required + type），列名与 schema properties 对应。
"""
import csv
import json
import sqlite3
from pathlib import Path

SCHEMA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "schemas"

TYPE_MAP = {
    "string": str,
    "number": (int, float),
    "integer": int,
    "boolean": (bool,),
}


def load_schema(name: str) -> dict:
    return json.loads((SCHEMA_DIR / f"{name}.json").read_text(encoding="utf-8"))


def coerce_row(row: dict, schema: dict) -> dict:
    """按 schema type 把 CSV 字符串转目标类型；转换失败抛 ValueError（显式失败，不静默）。"""
    out = {}
    types = {f: s.get("type") for f, s in schema.get("properties", {}).items()}
    for k, v in row.items():
        t = types.get(k)
        if v is None or v == "":
            out[k] = None
        elif t == "number":
            out[k] = float(v)
        elif t == "integer":
            out[k] = int(float(v))
        elif t == "boolean":
            out[k] = str(v).lower() in ("true", "1", "yes")
        else:
            out[k] = v
    return out


def validate_row(row: dict, schema: dict) -> list[str]:
    """返回错误列表；空列表 = 通过。draft-07 子集：required + 标量 type（先 coerce 再判类型）。"""
    errors = []
    for field in schema.get("required", []):
        if field not in row or row[field] in (None, ""):
            errors.append(f"缺必填字段: {field}")
    try:
        coerced = coerce_row(row, schema)
    except ValueError:
        return errors + ["字段类型转换失败（如数字列含非数字）"]
    for field, spec in schema.get("properties", {}).items():
        if coerced.get(field) is not None:
            expected = TYPE_MAP.get(spec.get("type"))
            if expected and not isinstance(coerced[field], expected):
                errors.append(f"字段类型错误: {field} 应为 {spec['type']}")
    return errors


def import_csv(csv_path: str | Path, schema_name: str, db_path: str | Path, table: str) -> dict:
    """导入 CSV 到 SQLite 表。返回 {imported: n, errors: [(行号, [错误])]}。有错行则整行跳过。"""
    schema = load_schema(schema_name)
    conn = sqlite3.connect(db_path)
    try:
        with open(csv_path, newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
        errors = []
        valid = []
        for i, row in enumerate(rows, start=2):  # 第 1 行是表头
            errs = validate_row(row, schema)
            if errs:
                errors.append((i, errs))
            else:
                valid.append(coerce_row(row, schema))
        if valid:
            cols = list(valid[0].keys())
            sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})"
            conn.executemany(sql, [[r[c] for c in cols] for r in valid])
            conn.commit()
        return {"imported": len(valid), "errors": errors}
    finally:
        conn.close()
