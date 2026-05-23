from __future__ import annotations

import time
from datetime import datetime, timezone
from urllib.parse import quote_plus

import requests

from .classifier import audio_use_for_category, classify_priority
from .config import AppConfig, STORES_FILE, TARGETS_FILE, load_yaml
from .extractors import get_extractor
from .normalizer import is_component_match
from .storage import stable_hash


def _fetch(session: requests.Session, url: str, cfg: AppConfig) -> str:
    for attempt in range(cfg.retries + 1):
        try:
            resp = session.get(url, timeout=cfg.timeout_seconds)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException:
            if attempt >= cfg.retries:
                raise
            time.sleep(cfg.backoff_seconds * (attempt + 1))
    return ""


def _store_search_url(store: dict[str, str], term: str) -> str:
    template = store.get("search_url") or store.get("base_url") or ""
    return template.format(query=quote_plus(term))


def run_scan(cfg: AppConfig | None = None) -> list[dict[str, str]]:
    cfg = cfg or AppConfig()
    targets = load_yaml(TARGETS_FILE).get("categories", {})
    stores = load_yaml(STORES_FILE).get("stores", [])
    scan_time = datetime.now(timezone.utc).isoformat()
    out: list[dict[str, str]] = []
    by_hash: dict[str, dict[str, str]] = {}

    def _score_item(x: dict[str, str]) -> tuple[int, int, int]:
        return (int(bool(x.get("price"))), int(bool(x.get("availability"))), len(x.get("title", "")))

    session = requests.Session()
    session.headers.update({"User-Agent": cfg.user_agent})

    for category, cdata in targets.items():
        for term in cdata.get("components", []):
            for store in stores:
                if not store.get("enabled", True):
                    continue
                if store.get("scope", "national") in {"international", "unknown"}:
                    continue
                url = _store_search_url(store, term)
                if not url:
                    continue
                base_url = store.get("base_url", url)
                extractor = get_extractor(store.get("extractor", "generic"))
                try:
                    html = _fetch(session, url, cfg)
                    candidates = extractor.extract(html, url, base_url, term)
                    if not candidates and store.get("extractor") != "generic":
                        candidates = get_extractor("generic").extract(html, url, base_url, term)
                except Exception:
                    candidates = []
                for cand in candidates:
                    if not is_component_match(term, cand.raw_text or ""):
                        continue
                    item = {
                        "term": term,
                        "category": category,
                        "store": store["name"],
                        "title": cand.title,
                        "price": cand.price or "",
                        "availability": cand.availability or "",
                        "link": cand.link or url,
                        "priority": classify_priority(term),
                        "audio_use": audio_use_for_category(category),
                        "scan_datetime": scan_time,
                    }
                    item["hash"] = stable_hash(item)
                    existing = by_hash.get(item["hash"])
                    if existing is None or _score_item(item) > _score_item(existing):
                        by_hash[item["hash"]] = item
                time.sleep(cfg.request_interval_seconds)
    out.extend(by_hash.values())
    return out
