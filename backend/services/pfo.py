from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET


def load_pfo(path: Path) -> dict:
    root = ET.parse(path).getroot()
    equities = []
    for node in root.findall("./Equity"):
        equities.append(
            {
                "index": int(node.attrib.get("Index", "0")),
                "filename": node.attrib.get("FileName", ""),
                "color": node.attrib.get("Color", "Blue"),
                "weight": float(node.attrib.get("Weight", "1")),
                "contract": float(node.attrib.get("Count", "1")),
                "active": node.attrib.get("Active", "1") in {"1", "true", "True"},
                "name": node.attrib.get("Name", ""),
            }
        )
    commission_node = root.find("./CommissionConfig")
    commission_config = {}
    if commission_node is not None:
        for k, v in commission_node.attrib.items():
            try:
                commission_config[k] = float(v)
            except ValueError:
                continue
    desc_node = root.find("./description")
    description = (desc_node.text or "") if desc_node is not None else ""
    return {
        "equities": equities,
        "commission_config": commission_config,
        "description": description,
    }


def save_pfo(
    path: Path,
    equities: list[dict],
    commission_config: dict | None = None,
    description: str | None = None,
) -> None:
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
                "Count": str(eq.get("contract", 1)),
                "Active": "1" if bool(eq.get("active", True)) else "0",
                "Name": str(eq.get("name", "")),
            },
        )
    if commission_config:
        attrs = {}
        for k, v in commission_config.items():
            if v is None:
                continue
            attrs[str(k)] = str(v)
        if attrs:
            ET.SubElement(root, "CommissionConfig", attrs)
    desc_el = ET.SubElement(root, "description")
    desc_el.text = str(description or "")

    tree = ET.ElementTree(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(path, encoding="utf-8", xml_declaration=True)
