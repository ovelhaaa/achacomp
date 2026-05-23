from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

from .price import parse_brl_price


def load_seen(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, dict[str, Any]] = {}
    for key, item in raw.items():
        out[key] = _normalize_seen_item(key, item)
    return out


def save_seen(path: Path, seen: dict[str, dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(seen, ensure_ascii=False, indent=2), encoding="utf-8")


def _to_float(value: Decimal | None) -> float | None:
    return float(value) if value is not None else None


def _normalize_seen_item(key: str, item: dict[str, Any]) -> dict[str, Any]:
    return {
        "stable_id": item.get("stable_id") or item.get("hash") or key,
        "normalized_component": item.get("normalized_component", ""),
        "search_term": item.get("search_term") or item.get("term", ""),
        "category": item.get("category", ""),
        "store_id": item.get("store_id", ""),
        "store_name": item.get("store_name") or item.get("store", ""),
        "title": item.get("title", ""),
        "normalized_title": item.get("normalized_title", ""),
        "link": item.get("link", ""),
        "first_seen": item.get("first_seen", ""),
        "last_seen": item.get("last_seen", ""),
        "times_seen": int(item.get("times_seen", 1)),
        "last_price_raw": item.get("last_price_raw") or item.get("price", ""),
        "last_price_value": item.get("last_price_value"),
        "min_price_value": item.get("min_price_value"),
        "max_price_value": item.get("max_price_value"),
        "previous_price_value": item.get("previous_price_value"),
        "last_availability": item.get("last_availability") or item.get("availability", ""),
        "previous_availability": item.get("previous_availability"),
        "status": item.get("status", "active"),
        "last_event": item.get("last_event", "seen_again"),
        "priority": item.get("priority", ""),
        "audio_use": item.get("audio_use", ""),
    }


def update_history(current_items: list[dict[str, Any]], seen: dict[str, dict[str, Any]], now: str, successful_store_ids: set[str] | None = None) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], dict[str, Any]]:
    successful_store_ids = successful_store_ids or set()
    current_ids = set()
    events: list[dict[str, Any]] = []

    for item in current_items:
        sid = item["hash"]
        current_ids.add(sid)
        existing = seen.get(sid)
        curr_price = parse_brl_price(item.get("price"))
        curr_av = (item.get("availability") or "").strip()
        base_event = "seen_again"
        is_new = existing is None
        is_returned = False

        if existing is None:
            existing = _normalize_seen_item(sid, {})
            existing["first_seen"] = now
            existing["times_seen"] = 0
            base_event = "new"
        elif existing.get("status") == "missing":
            is_returned = True
            base_event = "returned"

        previous_price = existing.get("last_price_value")
        existing["previous_price_value"] = previous_price
        existing["last_price_raw"] = item.get("price", "")
        existing["last_price_value"] = _to_float(curr_price)
        if curr_price is not None:
            prev_min = existing.get("min_price_value")
            prev_max = existing.get("max_price_value")
            val = float(curr_price)
            existing["min_price_value"] = val if prev_min is None else min(prev_min, val)
            existing["max_price_value"] = val if prev_max is None else max(prev_max, val)

        previous_av = existing.get("last_availability")
        has_prior_observation = int(existing.get("times_seen", 0)) > 0
        existing["previous_availability"] = previous_av
        existing["last_availability"] = curr_av
        existing.update({
            "stable_id": sid,
            "search_term": item.get("term", ""),
            "category": item.get("category", ""),
            "store_id": item.get("store_id", ""),
            "store_name": item.get("store", ""),
            "title": item.get("title", ""),
            "link": item.get("link", ""),
            "normalized_component": item.get("term", "").lower(),
            "normalized_title": item.get("title", "").lower(),
            "last_seen": now,
            "times_seen": int(existing.get("times_seen", 0)) + 1,
            "status": "active",
            "priority": item.get("priority", ""),
            "audio_use": item.get("audio_use", ""),
        })

        price_changed = False
        price_drop = False
        price_increase = False
        sig_drop = False
        price_delta = 0.0
        price_delta_percent = 0.0
        if previous_price is not None and curr_price is not None:
            price_delta = float(curr_price) - float(previous_price)
            if abs(price_delta) >= 0.01:
                price_changed = True
                price_drop = price_delta < 0
                price_increase = price_delta > 0
                if previous_price:
                    price_delta_percent = (price_delta / float(previous_price)) * 100.0
                sig_drop = price_drop and abs(price_delta_percent) >= 10

        availability_changed = has_prior_observation and previous_av is not None and previous_av != curr_av
        event = base_event
        if base_event == "seen_again":
            if price_drop:
                event = "price_drop"
            elif price_increase:
                event = "price_increase"
            elif availability_changed:
                event = "availability_changed"
            else:
                event = "unchanged"

        existing["last_event"] = event
        seen[sid] = existing

        item.update({
            "stable_id": sid,
            "status": "returned" if is_returned else "active",
            "is_new": is_new,
            "is_returned": is_returned,
            "price_changed": price_changed,
            "price_drop": price_drop,
            "price_drop_significant": sig_drop,
            "price_increase": price_increase,
            "price_delta": round(price_delta, 2) if price_changed else 0,
            "price_delta_percent": round(price_delta_percent, 2) if price_changed else 0,
            "availability_changed": availability_changed,
            "event": event,
            "first_seen": existing["first_seen"],
            "last_seen": existing["last_seen"],
            "times_seen": existing["times_seen"],
            "previous_price_value": previous_price,
            "last_price_value": existing["last_price_value"],
            "previous_availability": previous_av,
        })
        if event in {"new", "returned", "price_drop", "price_increase", "availability_changed"}:
            events.append(item.copy())

    missing = 0
    for sid, entry in seen.items():
        if sid in current_ids:
            continue
        entry_store_id = entry.get("store_id")
        store_was_successful = bool(entry_store_id) and entry_store_id in successful_store_ids
        legacy_without_store = not entry_store_id and bool(successful_store_ids)
        if entry.get("status") == "active" and (store_was_successful or legacy_without_store):
            entry["status"] = "missing"
            entry["last_event"] = "missing"
            missing += 1
            events.append({
                "stable_id": sid,
                "event": "missing",
                "status": "missing",
                "store_id": entry.get("store_id", ""),
                "store": entry.get("store_name", ""),
                "term": entry.get("search_term", ""),
                "category": entry.get("category", ""),
                "title": entry.get("title", ""),
                "last_seen": entry.get("last_seen", ""),
            })

    summary = {
        "generated_at": now,
        "items_total": len(current_items),
        "items_new": sum(1 for x in current_items if x.get("event") == "new"),
        "items_returned": sum(1 for x in current_items if x.get("event") == "returned"),
        "items_missing": missing,
        "items_price_drop": sum(1 for x in current_items if x.get("price_drop")),
        "items_price_drop_significant": sum(1 for x in current_items if x.get("price_drop_significant")),
        "items_price_increase": sum(1 for x in current_items if x.get("price_increase")),
        "items_availability_changed": sum(1 for x in current_items if x.get("availability_changed")),
        "events": events,
    }
    return current_items, seen, summary
