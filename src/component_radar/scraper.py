from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from urllib.parse import quote_plus

from .classifier import audio_use_for_category, classify_priority
from .config import AppConfig, STORES_FILE, TARGETS_FILE, load_yaml
from .extractors import get_extractor
from .http import HttpClient, probable_blocked_html, save_no_results_html
from .normalizer import is_component_match
from .storage import stable_hash

logger = logging.getLogger(__name__)


def _store_search_url(store: dict[str, str], term: str) -> str:
    template = store.get("search_url") or store.get("base_url") or ""
    if "{query}" not in template:
        if store.get("enabled", True):
            logger.warning("Store '%s' has no {query} in URL template; skipping", store.get("id", "unknown"))
        return ""
    return template.replace("{query}", quote_plus(term))


def _store_headers(store: dict[str, object]) -> dict[str, str]:
    headers: dict[str, str] = {}
    referer = store.get("referer")
    if isinstance(referer, str) and referer:
        headers["Referer"] = referer
    request_cfg = store.get("request")
    if isinstance(request_cfg, dict):
        request_headers = request_cfg.get("headers")
        if isinstance(request_headers, dict):
            headers.update({str(k): str(v) for k, v in request_headers.items()})
    return headers


def run_scan(cfg: AppConfig | None = None) -> tuple[list[dict[str, str]], list[dict[str, object]]]:
    cfg = cfg or AppConfig()
    targets = load_yaml(TARGETS_FILE).get("categories", {})
    stores = load_yaml(STORES_FILE).get("stores", [])
    scan_time = datetime.now(timezone.utc).isoformat()
    by_hash: dict[str, dict[str, str]] = {}
    store_status: dict[str, dict[str, object]] = {}

    def _score_item(x: dict[str, str]) -> tuple[int, int, int]:
        return (int(bool(x.get("price"))), int(bool(x.get("availability"))), len(x.get("title", "")))

    http_client = HttpClient(
        timeout=cfg.timeout_seconds,
        max_retries=cfg.retries,
        backoff_seconds=cfg.backoff_seconds,
        user_agent=cfg.user_agent,
    )

    for category, cdata in targets.items():
        for term in cdata.get("components", []):
            for store in stores:
                if not store.get("enabled", True):
                    continue
                scope = store.get("scope", "national")
                if scope in {"international", "unknown"}:
                    continue
                store_id = store["id"]
                status = store_status.setdefault(store_id, {"store_id": store_id, "success": True, "error": None, "items_found": 0})
                url = _store_search_url(store, term)
                if not url:
                    continue
                base_url = store.get("base_url", url)
                extractor = get_extractor(store.get("extractor", "generic"))
                headers = _store_headers(store)
                timeout = cfg.timeout_seconds
                request_cfg = store.get("request")
                if isinstance(request_cfg, dict) and request_cfg.get("timeout_seconds"):
                    timeout = float(request_cfg["timeout_seconds"])
                try:
                    response = http_client.get(url, headers=headers, timeout=timeout)
                    html = response.text
                    logger.info(
                        "store=%s term=%s status=%s content_type=%s bytes=%s redirected=%s final_url=%s",
                        store_id,
                        term,
                        response.status_code,
                        response.headers.get("Content-Type", ""),
                        len(response.content),
                        bool(response.history),
                        response.url,
                    )
                    if response.status_code >= 400:
                        status["success"] = False
                        status["error"] = f"HTTP {response.status_code}"
                        candidates = []
                    else:
                        candidates = extractor.extract(html, url, base_url, term)
                        if not candidates and store.get("extractor") != "generic":
                            candidates = get_extractor("generic").extract(html, url, base_url, term)
                        if not candidates:
                            save_no_results_html(html, store_id, term)
                        if probable_blocked_html(html):
                            status["probable_block"] = True
                            logger.warning("Possível bloqueio detectado store=%s term=%s", store_id, term)
                except Exception as exc:
                    status["success"] = False
                    status["error"] = str(exc)
                    logger.warning("Extractor failed for store '%s' term '%s': %s", store_id, term, exc)
                    candidates = []
                for cand in candidates:
                    if not is_component_match(term, cand.raw_text or ""):
                        continue
                    item = {
                        "term": term,
                        "category": category,
                        "store": store["name"],
                        "store_id": store_id,
                        "title": cand.title,
                        "price": cand.price or "",
                        "availability": cand.availability or "",
                        "link": cand.link or url,
                        "priority": classify_priority(term),
                        "audio_use": audio_use_for_category(category),
                        "scan_datetime": scan_time,
                        "scope": scope,
                    }
                    item["hash"] = stable_hash(item)
                    existing = by_hash.get(item["hash"])
                    if existing is None or _score_item(item) > _score_item(existing):
                        by_hash[item["hash"]] = item
                status["items_found"] = int(status["items_found"]) + len(candidates)
                time.sleep(cfg.request_interval_seconds)
    return list(by_hash.values()), list(store_status.values())
