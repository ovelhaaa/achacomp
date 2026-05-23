from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .base import ExtractedProduct, StoreExtractor

_PRICE_PATTERN = re.compile(r"(?:R\$\s*)?\d+[\.,]\d{2}")


def extract_price(text: str) -> str:
    m = _PRICE_PATTERN.search(text)
    return m.group(0) if m else ""


def extract_availability(text: str) -> str:
    low = text.lower()
    if "esgotado" in low or "indispon" in low:
        return "indisponível"
    if "em estoque" in low or "dispon" in low:
        return "disponível"
    return ""


class GenericExtractor(StoreExtractor):
    store_id = "generic"

    def extract(self, html: str, search_url: str, base_url: str, term: str) -> list[ExtractedProduct]:
        soup = BeautifulSoup(html, "html.parser")
        out: list[ExtractedProduct] = []
        for a in soup.select("a[href]"):
            title = " ".join(a.get_text(" ", strip=True).split())
            if len(title) < 4:
                continue
            link = urljoin(base_url, a.get("href", ""))
            text = " ".join((a.parent.get_text(" ", strip=True) if a.parent else title).split())
            out.append(
                ExtractedProduct(
                    title=title,
                    link=link,
                    raw_text=text,
                    price=extract_price(text),
                    availability=extract_availability(text),
                )
            )
        return out
