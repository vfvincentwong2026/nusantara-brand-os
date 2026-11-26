"""用 Instagram Graph API 的 business_discovery 抓品牌公开资料。

凭证只读环境变量 NBO_IG_USER_ID、NBO_IG_ACCESS_TOKEN。缺任何一个：
报「IG 未接通」，不发请求，不写快照，不填任何数字。

handle 只来自品牌清单 data/radar/brand_list_*.json 的 ig_handle。
清单写 null / 空，或雷达种子 BRANDS.ig 里的演示号，都不拿来猜。

不接入 build_localradar。没有 IG 快照时，站点上的演示标注保持原样。

接口以 Meta 文档为准（2026-08-12 的 Business Discovery 示例为 Graph v27.0）：
https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/business_discovery/
"""
import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from nbo.localradar import WIB

GRAPH_VERSION = "v27.0"
GRAPH_HOST = "https://graph.facebook.com"
MEDIA_LIMIT = 12
MEDIA_FIELDS = "timestamp,like_count,comments_count,permalink"
USER_FIELDS = "followers_count,media_count"
ENV_USER_ID = "NBO_IG_USER_ID"
ENV_ACCESS_TOKEN = "NBO_IG_ACCESS_TOKEN"
HANDLE_RE = re.compile(r"^@?[A-Za-z0-9._]{1,30}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
IG_USER_ID_RE = re.compile(r"^\d{5,32}$")
# Graph API 限流：4 应用级、17 用户级、32 主页级、613 自定义、80002 Instagram 账号调用过多。
RATE_LIMIT_CODES = frozenset({4, 17, 32, 613, 80002})
AUTH_CODES = frozenset({102, 190, 458, 459, 463, 467})
PERMISSION_CODES = frozenset({10, 200, 294, 298})

REPO_ROOT = Path(__file__).resolve().parents[3]
SNAPSHOT_DIR = REPO_ROOT / "data" / "radar"

NOT_CONNECTED = (
    "IG 未接通。未设置 NBO_IG_USER_ID 或 NBO_IG_ACCESS_TOKEN，"
    "未请求 Instagram Graph API，未写入快照。"
)


class IGError(Exception):
    pass


class IGNotConnected(IGError):
    def __init__(self):
        super().__init__(NOT_CONNECTED)


class IGRateLimitError(IGError):
    pass


class IGAuthError(IGError):
    pass


class IGBrandDataError(IGError):
    pass


class IGResponseError(IGError):
    pass


class IGTransportError(IGError):
    pass


def credentials_from_env(env: dict | None = None) -> tuple[str, str] | None:
    """只从环境变量读。缺一则返回 None，调用方不得发请求。"""
    source = env if env is not None else {}
    user_id = str(source.get(ENV_USER_ID) or "").strip()
    token = str(source.get(ENV_ACCESS_TOKEN) or "").strip()
    if not user_id or not token:
        return None
    return user_id, token


def _redact(text: str, token: str) -> str:
    if not text or not token:
        return text
    quoted = urllib.parse.quote(token, safe="")
    return text.replace(token, "[redacted]").replace(quoted, "[redacted]")


def _as_int(value, key: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise IGResponseError(f"{key} 不是整数")
    if value < 0:
        raise IGResponseError(f"{key} 为负数")
    return value


def _optional_int(item: dict, key: str) -> int | None:
    if key not in item or item[key] is None:
        return None
    return _as_int(item[key], key)


def parse_recorded_handle(raw) -> dict:
    """只接受清单里原样记下的一个用户名。不删字符、不改大小写、不从品牌名推断。"""
    if raw is None:
        return {"kind": "missing"}
    if not isinstance(raw, str):
        return {"kind": "invalid", "raw": str(raw)}
    text = raw.strip()
    if not text:
        return {"kind": "missing"}
    if not HANDLE_RE.fullmatch(text):
        return {"kind": "invalid", "raw": text}
    username = text[1:] if text.startswith("@") else text
    if not username or username in {".", ".."}:
        return {"kind": "invalid", "raw": text}
    seed = text if text.startswith("@") else f"@{username}"
    return {"kind": "ok", "raw": seed, "username": username}


def _normalize_name(name: str) -> str:
    text = str(name).split("（", 1)[0].split("(", 1)[0]
    return re.sub(r"\s+", " ", text.strip().casefold())


def _list_key(name: str, used: set[str]) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", _normalize_name(name)).strip("-") or "brand"
    key = f"list-{base}"
    n = 2
    while key in used:
        key = f"list-{base}-{n}"
        n += 1
    return key


def recorded_targets(brand_list: dict, brands: list[dict]) -> tuple[list[dict], list[dict]]:
    """返回 (要写入快照的已记录 handle, 雷达里未记录 handle 的品牌)。

    不读取 brands[].ig。那个字段在清单明确写「未找到」时仍可能是演示号。
    """
    rows = brand_list.get("brands") if isinstance(brand_list, dict) else None
    if not isinstance(rows, list):
        raise IGBrandDataError("品牌清单缺少 brands 数组，未请求、未写入快照。")
    radar_ids = {b["id"] for b in brands}
    by_name: dict[str, str] = {}
    for b in brands:
        by_name.setdefault(_normalize_name(b.get("name") or ""), b["id"])
    used: set[str] = set()
    targets: list[dict] = []
    for row in rows:
        if not isinstance(row, dict):
            raise IGBrandDataError("品牌清单有非对象条目，未请求、未写入快照。")
        parsed = parse_recorded_handle(row.get("ig_handle"))
        if parsed["kind"] == "missing":
            continue
        repo_id = row.get("repo_id")
        name = str(row.get("brand") or "")
        if isinstance(repo_id, str) and repo_id in radar_ids:
            key = repo_id
        elif _normalize_name(name) in by_name:
            key = by_name[_normalize_name(name)]
        else:
            key = _list_key(name, used)
        if key in used:
            raise IGBrandDataError(f"品牌 id 重复: {key}。未请求、未写入快照。")
        used.add(key)
        item = {
            "id": key,
            "brand": name,
            "seed_handle": parsed.get("raw"),
            "handle_source": "brand_list.ig_handle",
        }
        if parsed["kind"] == "ok":
            item["username"] = parsed["username"]
            item["status"] = "recorded"
        else:
            item["status"] = "invalid_handle"
        targets.append(item)
    skipped = [
        {"id": b["id"], "brand": b.get("name"), "reason": "未记录 handle"}
        for b in brands
        if b["id"] not in used
    ]
    return targets, skipped


def latest_brand_list_path(directory: str | Path = SNAPSHOT_DIR) -> Path | None:
    files = sorted(Path(directory).glob("brand_list_*.json"))
    return files[-1] if files else None


def load_brand_list(path: str | Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("brands"), list):
        raise IGBrandDataError(f"不是品牌清单: {path}")
    return data


def discovery_fields(username: str) -> str:
    return (
        f"business_discovery.username({username})"
        f"{{{USER_FIELDS},media.limit({MEDIA_LIMIT}){{{MEDIA_FIELDS}}}}}"
    )


def build_request_url(ig_user_id: str, username: str, access_token: str) -> str:
    if not IG_USER_ID_RE.fullmatch(ig_user_id):
        raise IGAuthError("NBO_IG_USER_ID 须为公司 Instagram 专业号的数字 id，未请求、未写入快照。")
    query = urllib.parse.urlencode(
        {"fields": discovery_fields(username), "access_token": access_token},
        quote_via=urllib.parse.quote,
    )
    return f"{GRAPH_HOST}/{GRAPH_VERSION}/{ig_user_id}?{query}"


def default_http_get(url: str, timeout: float = 20.0) -> tuple[int, object]:
    req = urllib.request.Request(
        url,
        method="GET",
        headers={"Accept": "application/json", "User-Agent": "nbo-radar-ig/0.1"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            status = resp.status
    except urllib.error.HTTPError as e:
        raw = e.read()
        status = e.code
    except (urllib.error.URLError, TimeoutError, OSError):
        raise IGTransportError("Instagram Graph API 网络错误，未写入快照。") from None
    try:
        body = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        body = {"error": {"message": "Instagram Graph API 返回了无法解析的响应", "type": "IGResponse"}}
    return status, body


def _error_dict(body: object) -> dict | None:
    if isinstance(body, dict) and isinstance(body.get("error"), dict):
        return body["error"]
    return None


def _misconfigured(err: dict) -> bool:
    msg = str(err.get("message") or "").lower()
    return "business_discovery" in msg and ("nonexisting field" in msg or "node type" in msg)


def classify_response(status: int, body: object) -> str:
    err = _error_dict(body)
    code = err.get("code") if err else None
    if isinstance(code, bool):
        code = None
    if status == 429 or code in RATE_LIMIT_CODES:
        return "rate_limit"
    if status in (401, 403) or code in AUTH_CODES or code in PERMISSION_CODES or (err and _misconfigured(err)):
        return "auth"
    if err or status >= 400:
        return "brand"
    if status == 200 and isinstance(body, dict) and isinstance(body.get("business_discovery"), dict):
        return "ok"
    return "brand"


def _public_error(status: int, body: object, token: str) -> dict:
    err = _error_dict(body) or {}
    out: dict = {"http_status": status}
    code = err.get("code")
    if isinstance(code, int) and not isinstance(code, bool):
        out["code"] = code
    sub = err.get("error_subcode")
    if isinstance(sub, int) and not isinstance(sub, bool):
        out["error_subcode"] = sub
    for key in ("type", "message", "fbtrace_id"):
        if isinstance(err.get(key), str):
            out[key] = _redact(err[key], token)
    if "message" not in out:
        out["message"] = "Instagram Graph API 拒绝了该 handle，未写入数字。"
    return out


def parse_business_discovery(body: dict) -> dict:
    """只抄接口返回的字段。缺 like_count 保持 null，不补 0。"""
    bd = body.get("business_discovery")
    if not isinstance(bd, dict):
        raise IGResponseError("响应缺少 business_discovery")
    account = {
        "id": bd.get("id") if isinstance(bd.get("id"), str) else None,
        "followers_count": _as_int(bd.get("followers_count"), "followers_count"),
        "media_count": _as_int(bd.get("media_count"), "media_count"),
    }
    media_obj = bd.get("media")
    items: list[dict] = []
    truncated = False
    if media_obj is not None:
        if not isinstance(media_obj, dict):
            raise IGResponseError("media 字段不是对象")
        data = media_obj.get("data") or []
        if not isinstance(data, list):
            raise IGResponseError("media.data 不是数组")
        for item in data:
            if not isinstance(item, dict):
                raise IGResponseError("media 条目不是对象")
            items.append({
                "id": item.get("id") if isinstance(item.get("id"), str) else None,
                "timestamp": item.get("timestamp") if isinstance(item.get("timestamp"), str) else None,
                "like_count": _optional_int(item, "like_count"),
                "comments_count": _optional_int(item, "comments_count"),
                "permalink": item.get("permalink") if isinstance(item.get("permalink"), str) else None,
            })
        cursors = media_obj.get("paging") if isinstance(media_obj.get("paging"), dict) else {}
        cursors = cursors.get("cursors") if isinstance(cursors, dict) else {}
        truncated = bool(isinstance(cursors, dict) and cursors.get("after"))
    return {"account": account, "media": items, "media_truncated": truncated}


def _base_entry(target: dict) -> dict:
    entry = {
        "brand": target["brand"],
        "seed_handle": target.get("seed_handle"),
        "handle_source": target["handle_source"],
    }
    if target.get("username"):
        entry["username"] = target["username"]
    return entry


def collect(
    *,
    env: dict,
    brand_list: dict,
    brands: list[dict],
    http_get=default_http_get,
    now: datetime | None = None,
    brand_list_name: str | None = None,
) -> dict:
    creds = credentials_from_env(env)
    if creds is None:
        raise IGNotConnected()
    ig_user_id, token = creds
    if not IG_USER_ID_RE.fullmatch(ig_user_id):
        raise IGAuthError("NBO_IG_USER_ID 须为公司 Instagram 专业号的数字 id，未请求、未写入快照。")
    targets, skipped = recorded_targets(brand_list, brands)
    if now is None:
        now = datetime.now(timezone.utc)
    elif now.tzinfo is None:
        raise IGBrandDataError("now 需要带时区")
    utc = now.astimezone(timezone.utc)
    local = now.astimezone(WIB)
    brands_out: dict = {}
    calls = 0
    for target in targets:
        if target["status"] != "recorded":
            entry = _base_entry(target)
            entry["status"] = "invalid_handle"
            entry["note"] = "已记录的 handle 不是单个 Instagram 用户名，未改写、未请求。"
            brands_out[target["id"]] = entry
            continue
        calls += 1
        url = build_request_url(ig_user_id, target["username"], token)
        try:
            status, body = http_get(url)
        except IGError:
            raise
        except Exception:
            raise IGTransportError("Instagram Graph API 请求失败，未写入快照。") from None
        kind = classify_response(status, body)
        if kind == "rate_limit":
            raise IGRateLimitError("Instagram Graph API 限流，已停止后续请求，未写入快照。")
        if status >= 500:
            raise IGTransportError("Instagram Graph API 服务器错误，未写入快照。")
        if kind == "auth":
            detail = _public_error(status, body, token)
            raise IGAuthError(f"IG 凭证或专业号配置被拒绝，未写入快照。{detail.get('message', '')}")
        entry = _base_entry(target)
        if kind != "ok":
            entry["status"] = "error"
            entry["error"] = _public_error(status, body, token)
            brands_out[target["id"]] = entry
            continue
        try:
            parsed = parse_business_discovery(body)
        except IGResponseError as exc:
            entry["status"] = "error"
            entry["error"] = {"http_status": status, "message": _redact(str(exc), token)}
            brands_out[target["id"]] = entry
            continue
        entry["status"] = "ok"
        entry.update(parsed)
        brands_out[target["id"]] = entry
    return {
        "schema": "nbo.radar.ig_snapshot/v1",
        "platform": "instagram",
        "fetched_at": utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "fetched_at_local": local.strftime("%Y-%m-%d %H:%M (UTC+7)"),
        "snapshot_date": local.strftime("%Y-%m-%d"),
        "source": "Instagram Graph API business_discovery",
        "graph_host": GRAPH_HOST,
        "graph_version": GRAPH_VERSION,
        "queried_ig_user_id": ig_user_id,
        "credential_source": f"env:{ENV_USER_ID},env:{ENV_ACCESS_TOKEN}",
        "brand_list": brand_list_name,
        "media_limit": MEDIA_LIMIT,
        "ig_calls_used": calls,
        "notes": [
            "只记录 business_discovery 返回的原始字段，不推算、不把缺失点赞补成 0。",
            "handle 只来自品牌清单 ig_handle；未记录的不请求。",
            "访问令牌不入库。本快照不接入站点重建。",
        ],
        "brands": brands_out,
        "skipped": skipped,
    }


def snapshot_path(directory: str | Path, day: str) -> Path:
    if not DATE_RE.fullmatch(day):
        raise IGBrandDataError(f"日期不合法: {day}")
    try:
        datetime.strptime(day, "%Y-%m-%d")
    except ValueError as exc:
        raise IGBrandDataError(f"日期不合法: {day}") from exc
    return Path(directory) / f"ig_snapshot_{day}.json"


def write_snapshot(snap: dict, directory: str | Path, day: str, token: str = "") -> Path:
    blob = json.dumps(snap, ensure_ascii=False, indent=2) + "\n"
    if token and len(token) >= 8 and (token in blob or urllib.parse.quote(token, safe="") in blob):
        raise IGError("快照含访问令牌，拒绝写入。")
    path = snapshot_path(directory, day)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(blob, encoding="utf-8")
    tmp.replace(path)
    return path


def main(
    argv: list[str] | None = None,
    *,
    env: dict | None = None,
    http_get=default_http_get,
    brands: list[dict] | None = None,
    brand_list: dict | None = None,
    brand_list_name: str | None = None,
    now: datetime | None = None,
) -> int:
    ap = argparse.ArgumentParser(description="抓取已记录的品牌 IG handle → ig_snapshot_YYYY-MM-DD.json")
    ap.add_argument("--out-dir", default=str(SNAPSHOT_DIR), help="快照目录，默认 data/radar")
    ap.add_argument("--date", default=None, help="文件名日期 YYYY-MM-DD，默认按 WIB 的当天")
    ap.add_argument("--brand-list", default=None, help="品牌清单 JSON，默认 data/radar 下最新一份")
    try:
        args = ap.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 2
    source_env = os_environ() if env is None else env
    creds = credentials_from_env(source_env)
    if creds is None:
        print(NOT_CONNECTED, file=sys.stderr)
        return 2
    token = creds[1]
    if brands is None:
        from nbo.localradar import BRANDS
        brands = BRANDS
    list_name = brand_list_name
    if brand_list is None:
        list_path = Path(args.brand_list) if args.brand_list else latest_brand_list_path()
        if list_path is None:
            print("没有品牌清单，无法确定已记录的 IG handle，未请求、未写入快照。", file=sys.stderr)
            return 5
        try:
            brand_list = load_brand_list(list_path)
        except (OSError, json.JSONDecodeError, IGBrandDataError) as exc:
            print(f"{exc} 未请求、未写入快照。", file=sys.stderr)
            return 5
        list_name = Path(list_path).name
    try:
        snap = collect(
            env=source_env,
            brand_list=brand_list,
            brands=brands,
            http_get=http_get,
            now=now,
            brand_list_name=list_name,
        )
    except IGNotConnected:
        print(NOT_CONNECTED, file=sys.stderr)
        return 2
    except IGRateLimitError as exc:
        print(_redact(str(exc), token), file=sys.stderr)
        return 3
    except IGAuthError as exc:
        print(_redact(str(exc), token), file=sys.stderr)
        return 4
    except IGBrandDataError as exc:
        print(_redact(str(exc), token), file=sys.stderr)
        return 5
    except (IGTransportError, IGResponseError) as exc:
        print(_redact(str(exc), token), file=sys.stderr)
        return 1
    day = args.date or snap["snapshot_date"]
    try:
        path = write_snapshot(snap, args.out_dir, day, token=token)
    except (IGError, OSError) as exc:
        print(_redact(str(exc), token), file=sys.stderr)
        return 1
    ok = sum(1 for b in snap["brands"].values() if b.get("status") == "ok")
    errors = sum(1 for b in snap["brands"].values() if b.get("status") == "error")
    print(json.dumps({
        "file": path.name,
        "fetched_at": snap["fetched_at"],
        "source": snap["source"],
        "ok": ok,
        "errors": errors,
        "skipped": len(snap["skipped"]),
        "ig_calls_used": snap["ig_calls_used"],
    }, ensure_ascii=False))
    return 0


def os_environ() -> dict:
    import os
    return os.environ


if __name__ == "__main__":
    sys.exit(main())
