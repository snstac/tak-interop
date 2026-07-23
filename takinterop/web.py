"""Packaged browser resources shared by TAK-aware web applications."""

from pathlib import Path


def web_assets_path() -> Path:
    """Return the directory containing shared, read-only browser assets."""

    return Path(__file__).with_name("web")
