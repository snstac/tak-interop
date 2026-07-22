"""Deterministic TAK Mission Package construction."""

from __future__ import annotations

import io
import uuid
import zipfile
from dataclasses import dataclass
from xml.etree import ElementTree as ET


CANONICAL_MANIFEST_PATH = "MANIFEST/manifest.xml"
LEGACY_MANIFEST_PATH = "MANIFEST/MANIFEST.xml"


def _safe_path(value: str) -> str:
    normalized = value.replace("\\", "/").strip("/")
    if not normalized or any(part in {"", ".", ".."} for part in normalized.split("/")):
        raise ValueError("mission package entry path is unsafe")
    return normalized


def _zip_info(path: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(path, (1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    info.create_system = 3
    return info


@dataclass(frozen=True)
class _Entry:
    path: str
    payload: bytes
    ignore: bool
    parameters: tuple[tuple[str, str], ...]


class MissionPackageBuilder:
    def __init__(
        self,
        name: str,
        *,
        uid: str | None = None,
        on_receive_delete: bool = True,
        manifest_path: str = CANONICAL_MANIFEST_PATH,
    ) -> None:
        if not name:
            raise ValueError("mission package name is required")
        self.name = name
        self.uid = uid or str(uuid.uuid5(uuid.NAMESPACE_URL, f"urn:tak-package:{name}"))
        self.on_receive_delete = on_receive_delete
        if manifest_path not in {CANONICAL_MANIFEST_PATH, LEGACY_MANIFEST_PATH}:
            raise ValueError("unsupported manifest path")
        self.manifest_path = manifest_path
        self._entries: dict[str, _Entry] = {}

    def add_bytes(
        self,
        path: str,
        payload: bytes | str,
        *,
        ignore: bool = False,
        parameters: dict[str, str] | None = None,
    ) -> None:
        entry_path = _safe_path(path)
        if entry_path.casefold() == self.manifest_path.casefold():
            raise ValueError("manifest path is reserved")
        if entry_path in self._entries:
            raise ValueError(f"duplicate mission package entry: {entry_path}")
        encoded = payload.encode("utf-8") if isinstance(payload, str) else bytes(payload)
        self._entries[entry_path] = _Entry(
            entry_path,
            encoded,
            ignore,
            tuple(sorted((str(key), str(value)) for key, value in (parameters or {}).items())),
        )

    def manifest_xml(self) -> bytes:
        root = ET.Element("MissionPackageManifest", {"version": "2"})
        configuration = ET.SubElement(root, "Configuration")
        for name, value in (
            ("name", self.name),
            ("uid", self.uid),
            ("onReceiveDelete", str(self.on_receive_delete).lower()),
        ):
            ET.SubElement(configuration, "Parameter", {"name": name, "value": value})
        contents = ET.SubElement(root, "Contents")
        for entry in sorted(self._entries.values(), key=lambda item: item.path):
            content = ET.SubElement(
                contents,
                "Content",
                {"ignore": str(entry.ignore).lower(), "zipEntry": entry.path},
            )
            for name, value in entry.parameters:
                ET.SubElement(content, "Parameter", {"name": name, "value": value})
        return b'<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="utf-8")

    def build(self) -> bytes:
        if not self._entries:
            raise ValueError("mission package has no contents")
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w") as archive:
            for entry in sorted(self._entries.values(), key=lambda item: item.path):
                archive.writestr(_zip_info(entry.path), entry.payload)
            archive.writestr(_zip_info(self.manifest_path), self.manifest_xml())
        return output.getvalue()
