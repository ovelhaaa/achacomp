from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExtractedProduct:
    title: str
    link: str
    price: str | None = None
    availability: str | None = None
    sku: str | None = None
    image_url: str | None = None
    raw_text: str | None = None


class StoreExtractor:
    store_id = "generic"

    def extract(self, html: str, search_url: str, base_url: str, term: str) -> list[ExtractedProduct]:
        raise NotImplementedError
