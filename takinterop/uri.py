"""TAK URI builders."""

from __future__ import annotations

from typing import Iterable, Mapping
from urllib.parse import quote, urlencode


def atak_import_uri(url: str) -> str:
    if not url.startswith(("https://", "http://")):
        raise ValueError("ATAK import URL must use HTTP(S)")
    return f"tak://com.atakmap.app/import?url={quote(url, safe='')}"


def atak_preference_uri(preferences: Iterable[Mapping[str, str]]) -> str:
    query: list[tuple[str, str]] = []
    for number, preference in enumerate(preferences, start=1):
        key = str(preference.get("key", ""))
        value_type = str(preference.get("type", ""))
        value = str(preference.get("value", ""))
        if not key or value_type not in {"string", "boolean", "integer", "float"}:
            raise ValueError("preference key and supported type are required")
        query.extend(
            ((f"key{number}", key), (f"type{number}", value_type), (f"value{number}", value))
        )
    if not query:
        raise ValueError("at least one preference is required")
    return "tak://com.atakmap.app/preference?" + urlencode(query)
