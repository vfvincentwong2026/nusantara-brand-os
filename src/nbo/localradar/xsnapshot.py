"""把 X 公开数据快照（data/radar/x_snapshot_YYYY-MM-DD.json）叠加到本地品牌雷达。

原则：
- 只用快照里 X 返回的原始数值，不推算、不补数；
- 每个字段带来源标记（provenance）：x_public = X 公开数据实抓，demo_estimate = 演示估算；
- handle 不存在/错误的品牌照实标注，不猜替代号（快照里只有经名称明确匹配的才写 resolved_handle）。

热度公式（仅用真实输入）：
    heat = round(100 * log10(1 + m7) / log10(1 + HEAT_REF_MENTIONS_7D), 1)，上限 100
    m7 = 近 7 天 X 全网提及该品牌的帖子数（排除转推，get_posts_counts_recent）
    HEAT_REF_MENTIONS_7D = 2000（7 天 2000 条提及 ≈ 满分 100）
原演示热度保留在 heat_demo 字段。
"""
import json
import math
from pathlib import Path

HEAT_REF_MENTIONS_7D = 2000
ACCOUNT_OK = ("ok", "replaced")
STATUS_CN = {
    "ok": "已核实",
    "replaced": "种子 handle 有误，已更正",
    "unverified_dormant": "账号存在但无法确认官方",
    "wrong_account": "种子 handle 指向无关账号",
    "not_found": "X 上不存在",
    "invalid": "handle 不合法",
}
DEMO_FIELDS = ("followers_wan", "views_wan", "likes_wan", "shares_wan", "er", "growth_30d",
               "why_hot", "viral_format", "need_supply", "need_social", "need_strategy",
               "ig", "tiktok")

REPO_ROOT = Path(__file__).resolve().parents[3]
SNAPSHOT_DIR = REPO_ROOT / "data" / "radar"


def latest_snapshot_path(directory: str | Path = SNAPSHOT_DIR) -> Path | None:
    files = sorted(Path(directory).glob("x_snapshot_*.json"))
    return files[-1] if files else None


def load_snapshot(path: str | Path) -> dict:
    snap = json.loads(Path(path).read_text(encoding="utf-8"))
    if snap.get("platform") != "x" or "brands" not in snap:
        raise ValueError(f"不是 X 雷达快照: {path}")
    return snap


def heat_from_mentions(m7: int) -> float:
    if m7 is None or m7 < 0:
        raise ValueError("m7 必须是非负整数")
    v = 100 * math.log10(1 + m7) / math.log10(1 + HEAT_REF_MENTIONS_7D)
    return round(min(v, 100.0), 1)


def _day(ts: str | None) -> str | None:
    return ts[:10] if ts else None


def apply_snapshot(brand: dict, snap: dict) -> dict:
    """返回叠加了 X 实抓数据的新 dict；快照里没有该品牌时原样返回（仍为 demo_seed）。"""
    b = dict(brand)
    prov = {f: "demo_estimate" for f in DEMO_FIELDS}
    prov.update({"heat": "demo_estimate", "heat_signals": "demo_estimate", "x": "demo_seed"})
    entry = snap["brands"].get(b["id"])
    if not entry:
        b["provenance"] = prov
        b["source_type"] = "demo_seed"
        return b

    fetched = snap.get("fetched_at")
    status = entry.get("handle_status")
    acct = entry.get("account") if status in ACCOUNT_OK else None
    mentions = entry.get("mentions_7d") or {}
    posts = entry.get("posts_30d") if acct else None

    b["x_seed_handle"] = entry.get("seed_handle")
    b["x_handle_status"] = status
    b["x_handle_note"] = entry.get("handle_note")
    b["x_fetched_at"] = fetched
    if acct:
        b["x"] = entry.get("resolved_handle") or entry.get("seed_handle")
        prov["x"] = "x_public"
    else:
        b["x"] = f"{entry.get('seed_handle')}（{STATUS_CN.get(status, status)}）"
        prov["x"] = "x_public_flagged"
    b["x_followers"] = acct["followers_count"] if acct else None
    b["x_tweet_count"] = acct["tweet_count"] if acct else None
    b["x_posts_30d"] = posts["count"] if posts else None
    b["x_posts_30d_likes"] = posts["likes"] if posts else None
    b["x_last_post_at"] = entry.get("last_post_at") if acct else None
    b["x_mentions_7d"] = mentions.get("total")
    b["x_mentions_query"] = mentions.get("query")
    b["x_mentions_noise"] = mentions.get("noise")
    for f in ("x_followers", "x_tweet_count", "x_posts_30d", "x_posts_30d_likes",
              "x_last_post_at", "x_mentions_7d"):
        prov[f] = "x_public" if b[f] is not None else "missing"

    b["heat_demo"] = brand["heat"]
    if b["x_mentions_7d"] is not None:
        b["heat"] = heat_from_mentions(b["x_mentions_7d"])
        prov["heat"] = "x_public"

    real = []
    if b["x_mentions_7d"] is not None:
        tail = f"（{mentions['note']}）" if mentions.get("note") else ""
        real.append(f"【X 实抓 {_day(fetched)}】近 7 天全网提及 {b['x_mentions_7d']:,} 条{tail}")
    if acct:
        bits = [f"官方号 {b['x']} 粉丝 {b['x_followers']:,}"]
        if b["x_posts_30d"] is not None:
            bits.append(f"近 30 天发帖 {b['x_posts_30d']}")
        elif b["x_tweet_count"] is not None:
            bits.append(f"累计发帖 {b['x_tweet_count']:,}")
        last = _day(b.get("x_last_post_at"))
        if last:
            bits.append(f"最近发帖 {last}")
        real.append(f"【X 实抓 {_day(fetched)}】" + " · ".join(bits))
    else:
        real.append(f"【X 实抓 {_day(fetched)}】{entry.get('seed_handle')}：{STATUS_CN.get(status, status)}")
    b["heat_signals_x"] = real
    b["heat_signals"] = real + [f"【演示】{s}" for s in brand.get("heat_signals", [])]
    prov["heat_signals"] = "mixed"
    prov["value_score"] = "mixed" if prov["heat"] == "x_public" else "demo_estimate"
    b["provenance"] = prov
    b["source_type"] = "mixed"   # X 字段实抓 + 其余演示估算
    return b
