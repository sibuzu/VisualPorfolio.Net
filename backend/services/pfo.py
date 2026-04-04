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
    date_range_node = root.find("./DateRangeConfig")
    date_range_config = {
        "enabled": False,
        "start": "",
        "end": "",
    }
    if date_range_node is not None:
        enabled_raw = str(
            date_range_node.attrib.get("enabled", date_range_node.attrib.get("use_range", "0"))
        )
        date_range_config["enabled"] = enabled_raw in {"1", "true", "True"}
        date_range_config["start"] = str(date_range_node.attrib.get("start", "") or "")
        date_range_config["end"] = str(date_range_node.attrib.get("end", "") or "")
    sharpe_node = root.find("./SharpeConfig")
    sharpe_config = {
        "capital": 1_000_000.0,
        "risk_free_rate": 0.0,
    }
    if sharpe_node is not None:
        raw_capital = sharpe_node.attrib.get("capital", "")
        raw_rf = sharpe_node.attrib.get("risk_free_rate", "")
        try:
            capital = float(raw_capital)
            if capital > 0:
                sharpe_config["capital"] = capital
        except (TypeError, ValueError):
            pass
        try:
            sharpe_config["risk_free_rate"] = float(raw_rf)
        except (TypeError, ValueError):
            pass
    return {
        "equities": equities,
        "commission_config": commission_config,
        "description": description,
        "date_range_config": date_range_config,
        "sharpe_config": sharpe_config,
    }


def save_pfo(
    path: Path,
    equities: list[dict],
    commission_config: dict | None = None,
    description: str | None = None,
    date_range_config: dict | None = None,
    sharpe_config: dict | None = None,
) -> None:
    root = _build_pfo_root(
        equities,
        commission_config=commission_config,
        description=description,
        date_range_config=date_range_config,
        sharpe_config=sharpe_config,
    )
    tree = ET.ElementTree(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(path, encoding="utf-8", xml_declaration=True)


def render_pfo_xml(
    equities: list[dict],
    commission_config: dict | None = None,
    description: str | None = None,
    date_range_config: dict | None = None,
    sharpe_config: dict | None = None,
) -> str:
    root = _build_pfo_root(
        equities,
        commission_config=commission_config,
        description=description,
        date_range_config=date_range_config,
        sharpe_config=sharpe_config,
    )
    xml_body = ET.tostring(root, encoding="unicode")
    return '<?xml version="1.0" encoding="utf-8"?>\n' + xml_body


def _build_pfo_root(
    equities: list[dict],
    commission_config: dict | None = None,
    description: str | None = None,
    date_range_config: dict | None = None,
    sharpe_config: dict | None = None,
) -> ET.Element:
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
    if date_range_config is not None:
        ET.SubElement(
            root,
            "DateRangeConfig",
            {
                "enabled": "1" if bool(date_range_config.get("enabled", False)) else "0",
                "start": str(date_range_config.get("start", "") or ""),
                "end": str(date_range_config.get("end", "") or ""),
            },
        )
    if sharpe_config is not None:
        ET.SubElement(
            root,
            "SharpeConfig",
            {
                "capital": str(sharpe_config.get("capital", 1_000_000.0)),
                "risk_free_rate": str(sharpe_config.get("risk_free_rate", 0.0)),
            },
        )
    return root
