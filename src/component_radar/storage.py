from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd

from .config import DATA_DIR, EVENTS_CSV, EVENTS_JSON, LATEST_CSV, LATEST_JSON, SEEN_JSON, SUMMARY_JSON
from .history import load_seen, save_seen, update_history as _update


def stable_hash(item: dict[str, Any]) -> str:
    base = "|".join([
        str(item.get("term", "")).upper(),
        str(item.get("store_id", item.get("store", "")).upper()),
        str(item.get("link", "")).strip(),
        str(item.get("title", "")).upper().strip(),
    ])
    return hashlib.sha256(base.encode("utf-8")).hexdigest()[:16]


def update_history(items: list[dict[str, Any]], scan_time_iso: str, successful_store_ids: set[str], seen_path: Path = SEEN_JSON) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    seen = load_seen(seen_path)
    items, seen, summary = _update(items, seen, scan_time_iso, successful_store_ids)
    save_seen(seen_path, seen)
    return items, summary


def save_latest(items: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_JSON.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.DataFrame(items).to_csv(LATEST_CSV, index=False)
    events = summary.pop("events", [])
    EVENTS_JSON.write_text(json.dumps(events, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.DataFrame(events).to_csv(EVENTS_CSV, index=False)
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
