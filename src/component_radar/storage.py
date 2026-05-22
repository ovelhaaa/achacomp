from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd

from .config import DATA_DIR, LATEST_CSV, LATEST_JSON, SEEN_JSON


def stable_hash(item: dict[str, Any]) -> str:
    base = "|".join([
        str(item.get("term", "")).upper(),
        str(item.get("store", "")).upper(),
        str(item.get("link", "")).strip(),
        str(item.get("title", "")).upper().strip(),
    ])
    return hashlib.sha256(base.encode("utf-8")).hexdigest()[:16]


def load_seen(path: Path = SEEN_JSON) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def update_history(items: list[dict[str, Any]], scan_time_iso: str, seen_path: Path = SEEN_JSON) -> list[dict[str, Any]]:
    seen = load_seen(seen_path)
    for item in items:
        key = item["hash"]
        if key in seen:
            item["is_new"] = False
            seen[key]["last_seen"] = scan_time_iso
        else:
            item["is_new"] = True
            seen[key] = {
                "hash": key,
                "term": item.get("term"),
                "title": item.get("title"),
                "store": item.get("store"),
                "first_seen": scan_time_iso,
                "last_seen": scan_time_iso,
            }
        item["first_seen"] = seen[key]["first_seen"]
        item["last_seen"] = seen[key]["last_seen"]

    seen_path.parent.mkdir(parents=True, exist_ok=True)
    seen_path.write_text(json.dumps(seen, ensure_ascii=False, indent=2), encoding="utf-8")
    return items


def save_latest(items: list[dict[str, Any]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_JSON.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.DataFrame(items).to_csv(LATEST_CSV, index=False)
