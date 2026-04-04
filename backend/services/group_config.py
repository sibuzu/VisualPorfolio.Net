from __future__ import annotations

import json
import re
from pathlib import Path


_DEFAULT_COLORS = ["#0a9396", "#bb3e03", "#005f73", "#ca6702"]
_SHARPE_CAPITAL_DEFAULT_WAN = 100.0


def _to_float(value, default: float = 1.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _load_json_tolerant(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        raw = path.read_text(encoding="utf-8-sig")
        cleaned = re.sub(r",(\s*[}\]])", r"\1", raw)
        obj = json.loads(cleaned)
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


def _save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _resolve_equity_filename(folder: Path, project_name: str) -> str:
    text = str(project_name or "").strip()
    if not text:
        return ""
    if text.lower().endswith((".sea", ".gsea")):
        return text
    sea = folder / f"{text}.sea"
    if sea.exists():
        return sea.name
    gsea = folder / f"{text}.gsea"
    if gsea.exists():
        return gsea.name
    return f"{text}.sea"


def load_group_equities(folder: Path) -> list[dict]:
    doc = _load_json_tolerant(folder / "group.json")
    group = doc.get("group")
    if not isinstance(group, list):
        return []

    equities: list[dict] = []
    for idx, item in enumerate(group):
        if not isinstance(item, dict):
            continue
        project = str(item.get("project", "")).strip()
        filename = _resolve_equity_filename(folder, project)
        if not filename:
            continue
        metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        color = str(metadata.get("color", _DEFAULT_COLORS[idx % len(_DEFAULT_COLORS)]))
        active = bool(metadata.get("active", True))
        name = str(item.get("project_name", "")).strip() or project
        equities.append(
            {
                "index": idx,
                "filename": filename,
                "color": color,
                "weight": _to_float(item.get("weight"), 1.0),
                "contract": _to_float(item.get("count"), 1.0),
                "active": active,
                "name": name or filename,
            }
        )
    return equities


def save_group_equities(folder: Path, equities: list[dict]) -> None:
    path = folder / "group.json"
    doc = _load_json_tolerant(path)
    group: list[dict] = []
    for i, eq in enumerate(equities):
        raw_filename = str(eq.get("filename", "")).strip()
        stem = Path(raw_filename).stem
        if not stem:
            continue
        color = str(eq.get("color", _DEFAULT_COLORS[i % len(_DEFAULT_COLORS)]))
        group.append(
            {
                "project": stem,
                "project_name": str(eq.get("name", stem) or stem),
                "count": _to_float(eq.get("contract"), 1.0),
                "weight": str(_to_float(eq.get("weight"), 1.0)),
                "metadata": {
                    "color": color,
                    "active": bool(eq.get("active", True)),
                },
            }
        )
    doc["group"] = group
    _save_json(path, doc)


def load_project_config(folder: Path) -> dict:
    doc = _load_json_tolerant(folder / "group.json")
    cfg = doc.get("project_config") if isinstance(doc.get("project_config"), dict) else {}
    commission = cfg.get("commission_config") if isinstance(cfg.get("commission_config"), dict) else {}
    date_range = cfg.get("date_range_config") if isinstance(cfg.get("date_range_config"), dict) else {}
    sharpe = cfg.get("sharpe_config") if isinstance(cfg.get("sharpe_config"), dict) else {}
    return {
        "commission_config": commission,
        "description": str(cfg.get("description", "") or ""),
        "date_range_config": {
            "enabled": bool(date_range.get("enabled", False)),
            "start": str(date_range.get("start", "") or ""),
            "end": str(date_range.get("end", "") or ""),
        },
        "sharpe_config": {
            "capital": _to_float(sharpe.get("capital"), _SHARPE_CAPITAL_DEFAULT_WAN),
            "risk_free_rate": _to_float(sharpe.get("risk_free_rate"), 0.0),
        },
    }


def save_project_config(
    folder: Path,
    commission_config: dict | None = None,
    description: str | None = None,
    date_range_config: dict | None = None,
    sharpe_config: dict | None = None,
) -> None:
    path = folder / "group.json"
    doc = _load_json_tolerant(path)
    existing = doc.get("project_config") if isinstance(doc.get("project_config"), dict) else {}
    cfg = dict(existing)
    if commission_config is not None:
        cfg["commission_config"] = commission_config
    if description is not None:
        cfg["description"] = str(description or "")
    if date_range_config is not None:
        cfg["date_range_config"] = {
            "enabled": bool(date_range_config.get("enabled", False)),
            "start": str(date_range_config.get("start", "") or ""),
            "end": str(date_range_config.get("end", "") or ""),
        }
    if sharpe_config is not None:
        cfg["sharpe_config"] = {
            "capital": _to_float(sharpe_config.get("capital"), _SHARPE_CAPITAL_DEFAULT_WAN),
            "risk_free_rate": _to_float(sharpe_config.get("risk_free_rate"), 0.0),
        }
    doc["project_config"] = cfg
    _save_json(path, doc)
