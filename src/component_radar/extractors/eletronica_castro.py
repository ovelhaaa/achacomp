from __future__ import annotations

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .base import ExtractedProduct, StoreExtractor
from .generic import extract_availability, extract_price


class EletronicaCastroExtractor(StoreExtractor):
    store_id = "eletronica_castro"

    def extract(self, html: str, search_url: str, base_url: str, term: str) -> list[ExtractedProduct]:
        soup = BeautifulSoup(html, "html.parser")
        items: list[ExtractedProduct] = []
        for node in soup.select(".w-100.float-left.link-name"):
            title = " ".join(node.get_text(" ", strip=True).split())
            if not title:
                continue
            anchor = node if node.name == "a" else node.find_parent("a")
            link = urljoin(base_url, anchor.get("href", "") if anchor else "")
            context_node = anchor.parent if anchor and anchor.parent else node.parent
            text = " ".join((context_node.get_text(" ", strip=True) if context_node else title).split())
            items.append(
                ExtractedProduct(
                    title=title,
                    link=link,
                    raw_text=text,
                    price=extract_price(text),
                    availability=extract_availability(text),
                )
            )
        return items
