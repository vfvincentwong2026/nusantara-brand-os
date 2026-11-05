#!/usr/bin/env python3
"""部署后的线上冒烟：请求 GitHub Pages，任一 URL 不是 HTTP 200 就失败。

只在 deploy 成功之后由工作流调用。tests/test_site_links.py 仍负责仓库里的
静态检查；这里打的是已经发布的站点。

检查四类地址：
1. 首页
2. 固定子页（带末尾斜杠）
3. 这些 HTML 以及它们引用的同站 JS 里的 href / src / fetch
4. web/**/*.json 里以 assets/ 开头的字符串（相对站点根）

外链（其它主机的 http/https）、mailto、data、javascript、tel、协议相对
地址，以及含 ${ 的模板占位，都不请求。查询串会先百分号编码再交给 curl，
避免中文标签被 shell 或 curl 拆坏后误报 404。
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote, urljoin, urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
BASE_URL = "https://vfvincentwong2026.github.io/nusantara-brand-os/"
SUBPAGES = (
    "map/",
    "library/",
    "tower/",
    "launch/",
    "brandkit/",
    "proposal/",
    "franchise/",
    "assembly/",
    "playbook/",
    "trend/",
)

# 与 tests/test_site_links.py 同一类链接：href / src / fetch("...")
LINK_RE = re.compile(
    r"""(?:\b(?:href|src)\s*=\s*|\bfetch\s*\(\s*)"""
    r"""(?P<q>['"])?(?P<raw>[^'"\s)>]*)"""
)
SKIP_PREFIXES = ("http:", "https:", "mailto:", "data:", "javascript:", "tel:", "//")
PATH_CHARS = re.compile(r"[A-Za-z0-9._~%/-]+")
USER_AGENT = "nusantara-brand-os-pages-smoke"
HOMEPAGE_ATTEMPTS = 5
HOMEPAGE_DELAY_SECONDS = 4
TRANSPORT_ATTEMPTS = 3
TRANSPORT_DELAY_SECONDS = 2
WORKERS = 8

Failure = tuple[str, int, str, str]  # url, status, origin, error


def encode_url(url: str) -> str:
    """百分号编码路径和查询串，且不把已经编码的 %XX 再编一次。"""
    parts = urlsplit(url.strip())
    path = quote(parts.path, safe="/%")
    query = quote(parts.query, safe="-._~=&%+") if parts.query else ""
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, query, ""))


def _host(url: str) -> str:
    return urlsplit(url).netloc.lower()


def _same_host(url: str) -> bool:
    return urlsplit(url).scheme in {"http", "https"} and _host(url) == _host(BASE_URL)


def _looks_like_path(path: str) -> bool:
    return "/" in path or "." in path


def resolve_same_site(page_url: str, raw: str) -> str | None:
    """把 href/src/fetch 的原始值解析成同站绝对 URL；外链和模板返回 None。"""
    if raw is None:
        return None
    raw = raw.strip()
    if not raw or "${" in raw:
        return None
    lowered = raw.lower()
    if lowered.startswith(("#", "?")):
        return None
    if lowered.startswith(("mailto:", "data:", "javascript:", "tel:", "blob:", "about:")):
        return None
    if lowered.startswith("//"):
        return None
    if lowered.startswith(("http:", "https:")):
        encoded = encode_url(raw.split("#", 1)[0])
        if not _same_host(encoded):
            return None
        return encoded
    path = raw.split("#", 1)[0].split("?", 1)[0]
    if not path or path.startswith("$") or not _looks_like_path(path):
        return None
    if not PATH_CHARS.fullmatch(path):
        return None
    absolute = urljoin(page_url, raw.split("#", 1)[0])
    encoded = encode_url(absolute)
    if not _same_host(encoded):
        return None
    return encoded


def extract_links(text: str, page_url: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for match in LINK_RE.finditer(text):
        url = resolve_same_site(page_url, match.group("raw"))
        if url and url not in seen:
            seen.add(url)
            found.append(url)
    return found


def _json_strings(node):
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for value in node.values():
            yield from _json_strings(value)
    elif isinstance(node, list):
        for value in node:
            yield from _json_strings(value)


def asset_string_url(value: str) -> str | None:
    """JSON 字符串里的 assets/... 解析到站点根下。其它值不检查。"""
    if not isinstance(value, str):
        return None
    if value.lower().startswith(SKIP_PREFIXES) or "${" in value:
        return None
    bare = value.split("#", 1)[0]
    path, _, query = bare.partition("?")
    if not path.startswith("assets/"):
        return None
    if not PATH_CHARS.fullmatch(path):
        return None
    url = BASE_URL + path
    if query:
        url += "?" + query
    return encode_url(url)


def json_asset_urls(web: Path) -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    seen: set[str] = set()
    root = web.parent
    for path in sorted(web.rglob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON {path}: {exc}") from exc
        source = str(path.relative_to(root))
        for value in _json_strings(data):
            url = asset_string_url(value)
            if url and url not in seen:
                seen.add(url)
                results.append((url, source))
    return results


def _is_javascript(url: str) -> bool:
    return urlsplit(url).path.endswith(".js")


def seed_urls() -> list[str]:
    home = encode_url(BASE_URL)
    return [home, *[encode_url(urljoin(BASE_URL, rel)) for rel in SUBPAGES]]


def run_smoke(
    request,
    web: Path,
    *,
    sleep=time.sleep,
    homepage_attempts: int = HOMEPAGE_ATTEMPTS,
    homepage_delay: float = HOMEPAGE_DELAY_SECONDS,
) -> tuple[dict[str, int], list[Failure]]:
    """请求种子页、同站链接和 JSON 资源。返回 (已检查状态, 失败列表)。"""
    if not web.is_dir():
        raise ValueError(f"missing web directory: {web}")

    seeds = seed_urls()
    home = seeds[0]
    status, body, error = 0, "", ""
    for attempt in range(1, homepage_attempts + 1):
        status, body, error = request(home, True)
        print(
            f"homepage attempt {attempt}/{homepage_attempts}: HTTP {status} {home}",
            flush=True,
        )
        if status == 200:
            break
        if attempt < homepage_attempts:
            sleep(homepage_delay)
    if status != 200:
        return {home: status}, [(home, status, "homepage", error)]

    checked: dict[str, tuple[int, str]] = {home: (200, "")}
    origins: dict[str, str] = {home: "seed"}
    bodies: dict[str, str] = {home: body}

    for url in seeds[1:]:
        page_status, text, err = request(url, True)
        checked[url] = (page_status, err)
        origins[url] = "seed"
        if page_status == 200:
            bodies[url] = text

    links: dict[str, str] = {}
    for page, text in bodies.items():
        for link in extract_links(text, page):
            links.setdefault(link, page)

    for url in [item for item in links if _is_javascript(item) and item not in bodies]:
        if url in checked and checked[url][0] != 200:
            continue
        js_status, text, err = request(url, True)
        checked[url] = (js_status, err)
        origins.setdefault(url, links[url])
        if js_status == 200:
            for link in extract_links(text, url):
                links.setdefault(link, url)

    for url, source in json_asset_urls(web):
        links.setdefault(url, source)

    pending = sorted(url for url in links if url not in checked)
    if pending:
        print(f"checking {len(pending)} linked urls", flush=True)
        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            futures = {pool.submit(request, url, False): url for url in pending}
            for future in futures:
                url = futures[future]
                link_status, _text, err = future.result()
                checked[url] = (link_status, err)
                origins.setdefault(url, links[url])

    failures: list[Failure] = []
    statuses: dict[str, int] = {}
    for url, (code, err) in sorted(checked.items()):
        statuses[url] = code
        if code != 200:
            failures.append((url, code, origins.get(url, ""), err))
    return statuses, failures


def curl_once(url: str, save_body: bool = False) -> tuple[int, str, str]:
    """用 curl 发一次 GET。--globoff 避免查询串里的 ? 和 [] 被当成通配。"""
    if save_body:
        handle = tempfile.NamedTemporaryFile(prefix="nbo-smoke-", suffix=".body", delete=False)
        handle.close()
        output = handle.name
    else:
        output = os.devnull
    cmd = [
        "curl",
        "--globoff",
        "--silent",
        "--show-error",
        "--location",
        "--max-redirs",
        "8",
        "--max-time",
        "30",
        "--user-agent",
        USER_AGENT,
        "--output",
        output,
        "--write-out",
        "%{http_code}",
        url,
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        return 0, "", "curl not found"
    code_text = (proc.stdout or "").strip()
    status = int(code_text) if code_text.isdigit() else 0
    error = (proc.stderr or "").strip()
    body = ""
    if save_body:
        try:
            body = Path(output).read_text(encoding="utf-8", errors="replace")
        finally:
            Path(output).unlink(missing_ok=True)
    if proc.returncode != 0 and not error:
        error = f"curl exit {proc.returncode}"
    return status, body, error


def curl_request(url: str, save_body: bool = False, *, sleep=time.sleep) -> tuple[int, str, str]:
    """HTTP 404 / 5xx 立即返回。没有拿到状态码时（网络失败）再试几次。"""
    last = (0, "", "")
    for attempt in range(1, TRANSPORT_ATTEMPTS + 1):
        last = curl_once(url, save_body)
        if last[0] != 0:
            return last
        if attempt < TRANSPORT_ATTEMPTS:
            sleep(TRANSPORT_DELAY_SECONDS)
    return last


def main() -> int:
    try:
        _statuses, failures = run_smoke(curl_request, WEB)
    except ValueError as exc:
        print(f"live smoke failed: {exc}", file=sys.stderr)
        return 1
    if failures:
        print(
            f"live smoke failed: {len(failures)} url(s) did not return HTTP 200",
            file=sys.stderr,
            flush=True,
        )
        for url, status, origin, error in failures:
            detail = f" ({error})" if error else ""
            print(f"FAIL {status} {url}{detail}", file=sys.stderr, flush=True)
            if origin:
                print(f"  from {origin}", file=sys.stderr, flush=True)
        return 1
    print(f"live smoke ok: {len(_statuses)} urls returned HTTP 200", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
