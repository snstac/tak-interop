"""Shared TAK interoperability primitives."""

from .kml import network_link_kml
from .mission import MissionPackageBuilder
from .products import Artifact, RelatedLink, TakAsset, TakProduct, product_catalog
from .uri import atak_import_uri, atak_preference_uri
from .validators import ValidationError, validate_path
from .web import web_assets_path

__all__ = [
    "Artifact",
    "MissionPackageBuilder",
    "RelatedLink",
    "TakAsset",
    "TakProduct",
    "ValidationError",
    "atak_import_uri",
    "atak_preference_uri",
    "network_link_kml",
    "product_catalog",
    "validate_path",
    "web_assets_path",
]

__version__ = "1.2.0"
