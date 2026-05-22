from __future__ import annotations

import re
import time
from datetime import datetime, timezone
from urllib.parse import quote_plus, urljoin

import requests
from bs4 import BeautifulSoup

from .classifier import audio_use_for_category, classify_priority
from .config import AppConfig, STORES_FILE, TARGETS_FILE, load_yaml
from .normalizer import is_component_match
from .storage import stable_hash

_PRICE_PATTERN = re.compile(r"(?:R\$\s*)?\d+[\.,]\d{2}")


def _extract_price(text: str) -> str:
    m = _PRICE_PATTERN.search(text)
    return m.group(0) if m else ""


def _extract_availability(text: str) -> str:
    low = text.lower()
    if "esgotado" in low or "indispon" in low:
        return "indisponível"
    if "em estoque" in low or "dispon" in low:
        return "disponível"
    return ""


def _extract_generic(html: str, base_url: str) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    out: list[dict[str, str]] = []
    for a in soup.select("a[href]"):
        title = " ".join(a.get_text(" ", strip=True).split())
        if len(title) < 4:
            continue
        link = urljoin(base_url, a.get("href", ""))
        text = " ".join((a.parent.get_text(" ", strip=True) if a.parent else title).split())
        out.append({
            "title": title,
            "link": link,
            "raw_text": text,
            "price": _extract_price(text),
            "availability": _extract_availability(text),
        })
    return out


def _extract_eletronica_castro(html: str, base_url: str) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    items: list[dict[str, str]] = []
    for node in soup.select(".w-100.float-left.link-name"):
        title = " ".join(node.get_text(" ", strip=True).split())
        if not title:
            continue
        anchor = node if node.name == "a" else node.find_parent("a")
        link = urljoin(base_url, anchor.get("href", "") if anchor else base_url)
        text = " ".join((anchor.parent.get_text(" ", strip=True) if anchor and anchor.parent else title).split())
        items.append({
            "title": title,
            "link": link,
            "raw_text": text,
            "price": _extract_price(text),
            "availability": _extract_availability(text),
        })
    return items or _extract_generic(html, base_url)


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


def run_scan(cfg: AppConfig | None = None) -> list[dict[str, str]]:
    cfg = cfg or AppConfig()
    targets = load_yaml(TARGETS_FILE).get("categories", {})
    stores = load_yaml(STORES_FILE).get("stores", [])
    scan_time = datetime.now(timezone.utc).isoformat()
    extractor_map = {"generic": _extract_generic, "eletronica_castro": _extract_eletronica_castro}
    out: list[dict[str, str]] = []

    session = requests.Session()
    session.headers.update({"User-Agent": cfg.user_agent})

    for category, cdata in targets.items():
        for term in cdata.get("components", []):
            for store in stores:
                url = store["base_url"].format(query=quote_plus(term))
                try:
                    html = _fetch(session, url, cfg)
                    candidates = extractor_map.get(store.get("extractor", "generic"), _extract_generic)(html, url)
                except Exception:
                    candidates = []
                for cand in candidates:
                    if not is_component_match(term, cand.get("raw_text", "")):
                        continue
                    item = {
                        "term": term,
                        "category": category,
                        "store": store["name"],
                        "title": cand.get("title", ""),
                        "price": cand.get("price", ""),
                        "availability": cand.get("availability", ""),
                        "link": cand.get("link", url),
                        "priority": classify_priority(term),
                        "audio_use": audio_use_for_category(category),
                        "scan_datetime": scan_time,
                    }
                    item["hash"] = stable_hash(item)
                    out.append(item)
                time.sleep(cfg.request_interval_seconds)
    return out
