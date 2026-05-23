from __future__ import annotations

from .bau_eletronica import BauEletronicaExtractor
from .base import ExtractedProduct, StoreExtractor
from .eletronica_castro import EletronicaCastroExtractor
from .generic import GenericExtractor
from .soldafria import SoldafriaExtractor


EXTRACTORS: dict[str, StoreExtractor] = {
    "generic": GenericExtractor(),
    "eletronica_castro": EletronicaCastroExtractor(),
    "soldafria": SoldafriaExtractor(),
    "bau_eletronica": BauEletronicaExtractor(),
}


def get_extractor(name: str | None) -> StoreExtractor:
    return EXTRACTORS.get(name or "generic", EXTRACTORS["generic"])


__all__ = ["ExtractedProduct", "StoreExtractor", "get_extractor"]
