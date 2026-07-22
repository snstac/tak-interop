"""Versioned TAK product catalog contract."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable
from urllib.parse import urlsplit


PRODUCT_KINDS = {
    "camera_catalog",
    "vector_layer",
    "raster_layer",
    "elevation",
    "bundle",
}


def _absolute_http_url(value: str, field_name: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username:
        raise ValueError(f"{field_name} must be an absolute HTTP(S) URL")
    return value


@dataclass(frozen=True)
class Artifact:
    rel: str
    media_type: str
    href: str
    title: str = ""

    def __post_init__(self) -> None:
        if not self.rel or not self.media_type:
            raise ValueError("artifact rel and media_type are required")
        _absolute_http_url(self.href, "artifact href")

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Artifact":
        return cls(
            rel=str(value["rel"]),
            media_type=str(value["media_type"]),
            href=str(value["href"]),
            title=str(value.get("title", "")),
        )


@dataclass(frozen=True)
class TakProduct:
    id: str
    name: str
    kind: str
    authority: str
    attribution: str
    terms_url: str
    artifacts: tuple[Artifact, ...]
    description: str = ""
    status: str = "available"
    access: str = "public"
    bounds: tuple[float, float, float, float] | None = None
    time_windows: tuple[str, ...] = field(default_factory=tuple)
    observed_at: str | None = None
    updated_at: str | None = None
    stale_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    schema_version: int = 1

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("unsupported TAK product schema version")
        if not self.id or any(character not in "abcdefghijklmnopqrstuvwxyz0123456789-._:" for character in self.id):
            raise ValueError("product id must be a lowercase stable identifier")
        if not self.name or self.kind not in PRODUCT_KINDS:
            raise ValueError("product name and supported kind are required")
        if not self.authority or not self.attribution:
            raise ValueError("product authority and attribution are required")
        _absolute_http_url(self.terms_url, "terms_url")
        if not self.artifacts:
            raise ValueError("product requires at least one artifact")
        if self.access not in {"public", "session", "bearer", "restricted"}:
            raise ValueError("unsupported product access policy")
        if self.bounds is not None:
            west, south, east, north = self.bounds
            if not (-180 <= west <= east <= 180 and -90 <= south <= north <= 90):
                raise ValueError("invalid product bounds")

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["artifacts"] = [asdict(item) for item in self.artifacts]
        value["time_windows"] = list(self.time_windows)
        value["bounds"] = list(self.bounds) if self.bounds is not None else None
        return {key: item for key, item in value.items() if item not in (None, "", [], {}, ())}

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "TakProduct":
        bounds = value.get("bounds")
        return cls(
            id=str(value["id"]),
            name=str(value["name"]),
            kind=str(value["kind"]),
            authority=str(value["authority"]),
            attribution=str(value["attribution"]),
            terms_url=str(value["terms_url"]),
            artifacts=tuple(Artifact.from_dict(item) for item in value["artifacts"]),
            description=str(value.get("description", "")),
            status=str(value.get("status", "available")),
            access=str(value.get("access", "public")),
            bounds=tuple(float(item) for item in bounds) if bounds is not None else None,  # type: ignore[arg-type]
            time_windows=tuple(str(item) for item in value.get("time_windows", [])),
            observed_at=value.get("observed_at"),
            updated_at=value.get("updated_at"),
            stale_at=value.get("stale_at"),
            metadata=dict(value.get("metadata", {})),
            schema_version=int(value.get("schema_version", 1)),
        )


def product_catalog(
    service: str,
    products: Iterable[TakProduct],
    *,
    generated_at: str,
) -> dict[str, Any]:
    items = sorted(products, key=lambda item: item.id)
    identifiers = [item.id for item in items]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("product IDs must be unique")
    return {
        "schema_version": 1,
        "service": service,
        "generated_at": generated_at,
        "items": [item.to_dict() for item in items],
        "count": len(items),
    }
