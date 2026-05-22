from __future__ import annotations

import re
import time
from datetime import datetime, timezone
from urllib.parse import quote_plus, urljoin
from urllib.request import Request, urlopen

from .classifier import audio_use_for_category, classify_priority
from .config import AppConfig, STORES_FILE, TARGETS_FILE, load_yaml
from .normalizer import is_component_match
from .storage import stable_hash


def _strip_html(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()


def _extract_generic(html: str, base_url: str) -> list[dict[str, str]]:
    out = []
    for m in re.finditer(r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.I | re.S):
        href = urljoin(base_url, m.group(1))
        title = _strip_html(m.group(2))
        if len(title) < 4:
            continue
        out.append({"title": title, "link": href, "raw_text": title})
    return out


def _extract_eletronica_castro(html: str, base_url: str) -> list[dict[str, str]]:
    matches = re.findall(r'<[^>]*class=["\'][^"\']*w-100 float-left link-name[^"\']*["\'][^>]*>(.*?)</[^>]+>', html, re.I | re.S)
    items = [{"title": _strip_html(t), "link": base_url, "raw_text": _strip_html(t)} for t in matches if _strip_html(t)]
    return items or _extract_generic(html, base_url)


def _fetch(url: str, cfg: AppConfig) -> str:
    req = Request(url, headers={"User-Agent": cfg.user_agent})
    for attempt in range(cfg.retries + 1):
        try:
            with urlopen(req, timeout=cfg.timeout_seconds) as resp:
                return resp.read().decode("utf-8", errors="ignore")
        except Exception:
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
    out = []
    for category, cdata in targets.items():
        for term in cdata.get("components", []):
            for store in stores:
                url = store["base_url"].format(query=quote_plus(term))
                try:
                    html = _fetch(url, cfg)
                    candidates = extractor_map.get(store.get("extractor", "generic"), _extract_generic)(html, url)
                except Exception:
                    candidates = []
                for cand in candidates:
                    if not is_component_match(term, cand.get("raw_text", "")):
                        continue
                    item = {"term": term, "category": category, "store": store["name"], "title": cand.get("title", ""), "price": "", "availability": "", "link": cand.get("link", url), "priority": classify_priority(term), "audio_use": audio_use_for_category(category), "scan_datetime": scan_time}
                    item["hash"] = stable_hash(item)
                    out.append(item)
                time.sleep(cfg.request_interval_seconds)
    return out
