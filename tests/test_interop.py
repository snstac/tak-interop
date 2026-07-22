from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from takinterop import (
    Artifact,
    MissionPackageBuilder,
    TakProduct,
    atak_import_uri,
    atak_preference_uri,
    network_link_kml,
    product_catalog,
    validate_path,
)


def test_mission_package_is_deterministic_and_valid(tmp_path: Path) -> None:
    def build() -> bytes:
        package = MissionPackageBuilder("test.zip", uid="test-uid")
        package.add_bytes("feeds/live.kml", network_link_kml("https://example.test/live.kml", title="Live"))
        package.add_bytes("maps/source.xml", "<customMapSource/>")
        return package.build()

    first = build()
    second = build()
    assert first == second
    path = tmp_path / "package.zip"
    path.write_bytes(first)
    assert validate_path(path)["kind"] == "mission_package"
    with zipfile.ZipFile(io.BytesIO(first)) as archive:
        assert archive.namelist() == [
            "feeds/live.kml",
            "maps/source.xml",
            "MANIFEST/manifest.xml",
        ]


def test_mission_package_rejects_unsafe_and_duplicate_paths() -> None:
    package = MissionPackageBuilder("test.zip")
    with pytest.raises(ValueError):
        package.add_bytes("../secret", b"")
    package.add_bytes("safe/file.txt", b"one")
    with pytest.raises(ValueError):
        package.add_bytes("safe/file.txt", b"two")


def test_uri_and_network_link_builders_encode_values() -> None:
    assert atak_import_uri("https://example.test/package.zip?a=1&b=two").endswith(
        "url=https%3A%2F%2Fexample.test%2Fpackage.zip%3Fa%3D1%26b%3Dtwo"
    )
    preference = atak_preference_uri(
        [{"key": "prefs_dted_stream", "type": "boolean", "value": "true"}]
    )
    assert "key1=prefs_dted_stream" in preference
    kml = network_link_kml("https://example.test/live.kml", title="Live")
    assert b'<kml xmlns="http://www.opengis.net/kml/2.2">' in kml
    assert ET.fromstring(kml).tag.endswith("kml")


def test_product_catalog_round_trip(tmp_path: Path) -> None:
    product = TakProduct(
        id="example-layer",
        name="Example",
        kind="vector_layer",
        authority="Example Agency",
        attribution="Example Agency",
        terms_url="https://example.test/terms",
        artifacts=(Artifact("geojson", "application/geo+json", "https://example.test/layer.geojson"),),
        bounds=(-124.5, 32.0, -114.0, 42.2),
        time_windows=("24h", "48h"),
    )
    value = product_catalog("example", [product], generated_at="2026-07-22T00:00:00Z")
    path = tmp_path / "products.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    assert validate_path(path) == {"valid": True, "kind": "product_catalog", "products": 1}
