from __future__ import annotations

from .base import ExtractedProduct, StoreExtractor
from .generic import GenericExtractor


class SoldafriaExtractor(StoreExtractor):
    store_id = "soldafria"

    def __init__(self) -> None:
        self._fallback = GenericExtractor()

    def extract(self, html: str, search_url: str, base_url: str, term: str) -> list[ExtractedProduct]:
        # Estrutura de busca pode variar com frequência; fallback seguro por enquanto.
        return self._fallback.extract(html, search_url, base_url, term)
