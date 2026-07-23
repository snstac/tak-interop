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

PRODUCT_DOMAINS = {"fire", "disaster", "usar"}
ASSET_STATES = {"live", "historical", "tombstone"}


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
class RelatedLink:
    rel: str
    href: str
    title: str = ""
    media_type: str = ""

    def __post_init__(self) -> None:
        if not self.rel:
            raise ValueError("link rel is required")
        _absolute_http_url(self.href, "link href")

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "RelatedLink":
        return cls(
            rel=str(value["rel"]),
            href=str(value["href"]),
            title=str(value.get("title", "")),
            media_type=str(value.get("media_type", "")),
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
    canonical_url: str = ""
    domains: tuple[str, ...] = field(default_factory=tuple)
    links: tuple[RelatedLink, ...] = field(default_factory=tuple)
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
        if self.canonical_url:
            _absolute_http_url(self.canonical_url, "canonical_url")
        if set(self.domains) - PRODUCT_DOMAINS:
            raise ValueError("unsupported product domain")
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
        value["domains"] = list(self.domains)
        value["links"] = [asdict(item) for item in self.links]
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
            canonical_url=str(value.get("canonical_url", "")),
            domains=tuple(str(item) for item in value.get("domains", [])),
            links=tuple(RelatedLink.from_dict(item) for item in value.get("links", [])),
            schema_version=int(value.get("schema_version", 1)),
        )


@dataclass(frozen=True)
class TakAsset:
    id: str
    name: str
    kind: str
    lifecycle_state: str
    source_id: str
    source_name: str
    authority: str
    attribution: str
    terms_url: str
    canonical_url: str
    product_ids: tuple[str, ...]
    domains: tuple[str, ...]
    geometry: dict[str, Any] | None = None
    properties: dict[str, Any] = field(default_factory=dict)
    observed_at: str | None = None
    updated_at: str | None = None
    first_seen_at: str | None = None
    last_seen_at: str | None = None
    retired_at: str | None = None
    expires_at: str | None = None
    links: tuple[RelatedLink, ...] = field(default_factory=tuple)
    schema_version: int = 1

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("unsupported TAK asset schema version")
        if not self.id or "/" in self.id or self.id in {".", ".."}:
            raise ValueError("asset id must be a stable path-safe identifier")
        if not self.name or not self.kind or not self.source_id or not self.source_name:
            raise ValueError("asset identity and source are required")
        if self.lifecycle_state not in ASSET_STATES:
            raise ValueError("unsupported asset lifecycle state")
        if not self.authority or not self.attribution or not self.product_ids:
            raise ValueError("asset authority, attribution, and product membership are required")
        _absolute_http_url(self.terms_url, "terms_url")
        _absolute_http_url(self.canonical_url, "canonical_url")
        if set(self.domains) - PRODUCT_DOMAINS:
            raise ValueError("unsupported asset domain")
        if self.lifecycle_state == "tombstone" and self.geometry is not None:
            raise ValueError("tombstone assets cannot retain geometry")

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["product_ids"] = list(self.product_ids)
        value["domains"] = list(self.domains)
        value["links"] = [asdict(item) for item in self.links]
        return {key: item for key, item in value.items() if item not in (None, "", [], {}, ())}

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "TakAsset":
        return cls(
            id=str(value["id"]),
            name=str(value["name"]),
            kind=str(value["kind"]),
            lifecycle_state=str(value["lifecycle_state"]),
            source_id=str(value["source_id"]),
            source_name=str(value["source_name"]),
            authority=str(value["authority"]),
            attribution=str(value["attribution"]),
            terms_url=str(value["terms_url"]),
            canonical_url=str(value["canonical_url"]),
            product_ids=tuple(str(item) for item in value["product_ids"]),
            domains=tuple(str(item) for item in value.get("domains", [])),
            geometry=dict(value["geometry"]) if value.get("geometry") is not None else None,
            properties=dict(value.get("properties", {})),
            observed_at=value.get("observed_at"),
            updated_at=value.get("updated_at"),
            first_seen_at=value.get("first_seen_at"),
            last_seen_at=value.get("last_seen_at"),
            retired_at=value.get("retired_at"),
            expires_at=value.get("expires_at"),
            links=tuple(RelatedLink.from_dict(item) for item in value.get("links", [])),
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
