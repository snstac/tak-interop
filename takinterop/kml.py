"""Small KML interoperability helpers."""

from __future__ import annotations

from xml.etree import ElementTree as ET


KML_NS = "http://www.opengis.net/kml/2.2"


def network_link_kml(url: str, *, title: str, refresh_seconds: int = 120) -> bytes:
    if not url.startswith(("https://", "http://")):
        raise ValueError("network link URL must use HTTP(S)")
    if refresh_seconds < 15:
        raise ValueError("network link refresh must be at least 15 seconds")
    ET.register_namespace("", KML_NS)
    root = ET.Element(f"{{{KML_NS}}}kml")
    document = ET.SubElement(root, f"{{{KML_NS}}}Document")
    ET.SubElement(document, f"{{{KML_NS}}}name").text = title
    link = ET.SubElement(document, f"{{{KML_NS}}}NetworkLink")
    ET.SubElement(link, f"{{{KML_NS}}}name").text = title
    target = ET.SubElement(link, f"{{{KML_NS}}}Link")
    ET.SubElement(target, f"{{{KML_NS}}}href").text = url
    ET.SubElement(target, f"{{{KML_NS}}}refreshMode").text = "onInterval"
    ET.SubElement(target, f"{{{KML_NS}}}refreshInterval").text = str(refresh_seconds)
    return b'<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="utf-8")
