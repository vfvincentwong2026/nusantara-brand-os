"""GitHub Pages 站点根是 web/，线上挂在 /nusantara-brand-os/ 下。

同站链接若以 "/" 开头，会打到用户页根而不是本项目，全部 404。
本测试只检查 web/ 下的 html 与 js：根绝对路径一律失败；相对路径必须能落到
web/ 里的文件，或落到带 index.html 的目录。外链不检查。
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"

# href/src 属性、fetch("...")、url(...)
LINK_RE = re.compile(
    r"""(?:\b(?:href|src)\s*=\s*|\bfetch\s*\(\s*|\burl\(\s*)"""
    r"""(?P<q>['"])?(?P<raw>[^'"\s)>]*)""",
    re.IGNORECASE,
)
SKIP_PREFIXES = ("http:", "https:", "mailto:", "data:", "javascript:", "tel:", "//")
PATH_CHARS = re.compile(r"[A-Za-z0-9._~%/-]+")


def _sources():
    for path in WEB.rglob("*"):
        if path.is_file() and path.suffix in {".html", ".js"}:
            yield path


def _looks_like_path(raw: str) -> bool:
    """Ignore fetch(u) / url(t) identifiers. Real links contain a slash or a dot."""
    return "/" in raw or "." in raw


def _static_target(raw: str) -> str | None:
    """Return the path to resolve, or None when the link is not a static file."""
    if not raw or raw.startswith("#") or raw.startswith("?"):
        return None
    if raw.startswith(SKIP_PREFIXES) or not _looks_like_path(raw):
        return None
    path = raw.split("#", 1)[0].split("?", 1)[0]
    if not path or "${" in path or path.startswith("$"):
        return None
    if not PATH_CHARS.fullmatch(path):
        return None
    return path


def test_no_root_absolute_same_site_links():
    offenders = []
    for path in _sources():
        text = path.read_text(encoding="utf-8")
        for match in LINK_RE.finditer(text):
            raw = match.group("raw")
            if raw.startswith("/") and not raw.startswith("//"):
                line = text.count("\n", 0, match.start()) + 1
                offenders.append(f"{path.relative_to(ROOT)}:{line}: {raw}")
    assert not offenders, "同站根绝对路径会在 GitHub Pages 子路径下 404:\n" + "\n".join(offenders)


def test_relative_links_resolve_under_web():
    missing = []
    for path in _sources():
        text = path.read_text(encoding="utf-8")
        for match in LINK_RE.finditer(text):
            raw = match.group("raw")
            if raw.startswith("/") or raw.startswith(SKIP_PREFIXES):
                continue
            target_rel = _static_target(raw)
            if target_rel is None:
                continue
            target = (path.parent / target_rel).resolve()
            try:
                target.relative_to(WEB.resolve())
            except ValueError:
                line = text.count("\n", 0, match.start()) + 1
                missing.append(f"{path.relative_to(ROOT)}:{line}: {raw} 逃出 web/")
                continue
            ok = target.is_file() or (target.is_dir() and (target / "index.html").is_file())
            if not ok:
                line = text.count("\n", 0, match.start()) + 1
                missing.append(f"{path.relative_to(ROOT)}:{line}: {raw}")
    assert not missing, "相对链接在 web/ 下没有对应文件或目录 index.html:\n" + "\n".join(missing)
