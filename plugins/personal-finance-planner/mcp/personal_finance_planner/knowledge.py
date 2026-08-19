"""Versioned public knowledge-card loader."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


PLUGIN_ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE_DIR = PLUGIN_ROOT / "knowledge" / "v0.1.0"


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a mapping in {path}")
    return value


def catalog() -> dict[str, Any]:
    return _load_yaml(KNOWLEDGE_DIR / "catalog.yaml")


def card(card_id: str) -> dict[str, Any]:
    catalog_value = catalog()
    entries = {item["id"]: item for item in catalog_value["cards"]}
    if card_id not in entries:
        raise KeyError(f"Unknown knowledge card: {card_id}")
    return _load_yaml(KNOWLEDGE_DIR / entries[card_id]["file"])


def catalog_as_json() -> str:
    return json.dumps(catalog(), ensure_ascii=False, indent=2)


def card_as_json(card_id: str) -> str:
    return json.dumps(card(card_id), ensure_ascii=False, indent=2)
