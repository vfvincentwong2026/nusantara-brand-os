"""Paths written into web/*.json.

GitHub Pages serves this repo under /nusantara-brand-os/. A value that starts
with "/" is requested from the user-site root and 404s. Asset paths are stored
relative to web/ with no leading slash; pages resolve them with
web/ui/sitepath.js. Pages that live on the container site are absolute URLs.
"""
CONTAINER_ORIGIN = "https://nusantara-container.pages.dev"


def asset(path: str) -> str:
    """Site-root-relative path under web/, without a leading slash."""
    return path.lstrip("/")


def container(path: str) -> str:
    """Absolute URL on the container site. path may include a query string."""
    if not path.startswith("/"):
        path = "/" + path
    return CONTAINER_ORIGIN + path
