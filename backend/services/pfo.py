from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET


def load_pfo(path: Path) -> list[dict]:
    root = ET.parse(path).getroot()
    equities = []
    for node in root.findall("./Equity"):
        equities.append(
            {
                "index": int(node.attrib.get("Index", "0")),
                "filename": node.attrib.get("FileName", ""),
                "color": node.attrib.get("Color", "Blue"),
                "weight": float(node.attrib.get("Weight", "1")),
                "contract": float(node.attrib.get("Contract", "1")),
                "active": node.attrib.get("Active", "1") in {"1", "true", "True"},
                "name": node.attrib.get("Name", ""),
            }
        )
    return equities


def save_pfo(path: Path, equities: list[dict]) -> None:
    root = ET.Element("PortfolioyList")
    for eq in equities:
        ET.SubElement(
            root,
            "Equity",
            {
                "Index": str(eq.get("index", 0)),
                "FileName": str(eq.get("filename", "")),
                "Color": str(eq.get("color", "Blue")),
                "Weight": str(eq.get("weight", 1)),
                "Contract": str(eq.get("contract", 1)),
                "Active": "1" if bool(eq.get("active", True)) else "0",
                "Name": str(eq.get("name", "")),
            },
        )

    tree = ET.ElementTree(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(path, encoding="utf-8", xml_declaration=True)
