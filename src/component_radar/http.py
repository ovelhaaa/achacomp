from __future__ import annotations

import logging
import os
import re
import time
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
}

BLOCK_PATTERNS = ["access denied", "forbidden", "captcha", "cloudflare", "attention required", "robot", "blocked"]


class HttpClient:
    def __init__(
        self,
        timeout: float = 20.0,
        max_retries: int = 2,
        backoff_seconds: float = 2.0,
        user_agent: str | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds
        self.session = session or requests.Session()
        headers = dict(DEFAULT_HEADERS)
        env_ua = os.getenv("COMPONENT_RADAR_USER_AGENT")
        headers["User-Agent"] = user_agent or env_ua or headers["User-Agent"]
        self.session.headers.update(headers)

    def get(self, url: str, headers: dict[str, str] | None = None, timeout: float | None = None) -> requests.Response:
        merged = dict(headers or {})
        timeout_s = timeout if timeout is not None else self.timeout
        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.get(url, timeout=timeout_s, headers=merged or None)
            except requests.RequestException:
                if attempt >= self.max_retries:
                    raise
                self._sleep(attempt, 0)
                continue

            if response.status_code in {403, 429, 503} and attempt < self.max_retries:
                self._sleep(attempt, response.status_code)
                continue
            return response
        raise requests.RequestException(f"Falha ao requisitar URL: {url}")

    def _sleep(self, attempt: int, status_code: int) -> None:
        multiplier = 2 if status_code in {403, 429, 503} else 1
        time.sleep(self.backoff_seconds * (attempt + 1) * multiplier)


def probable_blocked_html(html: str) -> bool:
    low = html.lower()
    return any(p in low for p in BLOCK_PATTERNS)


def sanitize_filename(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    return safe.strip("._-") or "term"


def save_no_results_html(html: str, store_id: str, term: str, root: Path | None = None) -> Path:
    base = root or Path("data")
    out_dir = base / "debug" / "no_results"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{sanitize_filename(store_id)}_{sanitize_filename(term)}.html"
    path.write_text(html, encoding="utf-8")
    return path
