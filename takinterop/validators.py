"""Validation entry points for generated TAK artifacts."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from .mission import CANONICAL_MANIFEST_PATH, LEGACY_MANIFEST_PATH
from .products import TakProduct


class ValidationError(ValueError):
    pass


def _safe_member(name: str) -> bool:
    normalized = name.replace("\\", "/")
    return bool(normalized) and not normalized.startswith("/") and all(
        part not in {"", ".", ".."} for part in normalized.split("/")
    )


def validate_zip(path: Path) -> dict[str, object]:
    try:
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            if not names or not all(_safe_member(name) for name in names):
                raise ValidationError("archive contains an unsafe or empty member")
            manifest_name = next(
                (name for name in (CANONICAL_MANIFEST_PATH, LEGACY_MANIFEST_PATH) if name in names),
                None,
            )
            if manifest_name is None:
                if path.suffix.lower() == ".kmz" and "doc.kml" in names:
                    ET.fromstring(archive.read("doc.kml"))
                    return {"valid": True, "kind": "kmz", "members": len(names)}
                raise ValidationError("Mission Package manifest is missing")
            root = ET.fromstring(archive.read(manifest_name))
            if root.tag != "MissionPackageManifest" or root.attrib.get("version") != "2":
                raise ValidationError("Mission Package manifest root is invalid")
            referenced = {
                element.attrib.get("zipEntry", "") for element in root.findall("./Contents/Content")
            }
            missing = referenced - set(names)
            if missing:
                raise ValidationError(f"Mission Package content is missing: {sorted(missing)[0]}")
            return {"valid": True, "kind": "mission_package", "members": len(names)}
    except (OSError, zipfile.BadZipFile, ET.ParseError) as error:
        raise ValidationError(str(error)) from error


def validate_xml(path: Path) -> dict[str, object]:
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as error:
        raise ValidationError(str(error)) from error
    local_name = root.tag.rsplit("}", 1)[-1]
    if local_name not in {"kml", "event", "customMapSource", "preferences"}:
        raise ValidationError(f"unsupported XML root: {local_name}")
    return {"valid": True, "kind": local_name}


def validate_catalog(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        if value.get("schema_version") != 1 or not isinstance(value.get("items"), list):
            raise ValidationError("invalid TAK product catalog")
        products = [TakProduct.from_dict(item) for item in value["items"]]
        if int(value.get("count", -1)) != len(products):
            raise ValidationError("catalog count does not match items")
        if len({item.id for item in products}) != len(products):
            raise ValidationError("catalog product IDs are not unique")
        return {"valid": True, "kind": "product_catalog", "products": len(products)}
    except (OSError, TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
        if isinstance(error, ValidationError):
            raise
        raise ValidationError(str(error)) from error


def validate_path(value: str | Path) -> dict[str, object]:
    path = Path(value)
    suffix = path.suffix.lower()
    if suffix in {".zip", ".kmz"}:
        return validate_zip(path)
    if suffix in {".xml", ".kml", ".cot", ".pref"}:
        return validate_xml(path)
    if suffix == ".json":
        return validate_catalog(path)
    raise ValidationError(f"unsupported artifact extension: {suffix or '<none>'}")
