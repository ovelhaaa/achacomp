from __future__ import annotations

from .base import ExtractedProduct, StoreExtractor
from .generic import GenericExtractor


class BauEletronicaExtractor(StoreExtractor):
    store_id = "bau_eletronica"

    def __init__(self) -> None:
        self._fallback = GenericExtractor()

    def extract(self, html: str, search_url: str, base_url: str, term: str) -> list[ExtractedProduct]:
        # Estrutura de busca pode variar; manter fallback genérico robusto nesta etapa.
        return self._fallback.extract(html, search_url, base_url, term)
