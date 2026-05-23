from __future__ import annotations

from collections import Counter

from bs4 import BeautifulSoup

KEYWORDS = {
    "title": ["product", "produto", "item", "name", "nome", "title", "titulo", "link-name"],
    "price": ["price", "preco", "valor"],
    "availability": ["stock", "estoque", "available", "disponivel"],
}


def _selector_for(tag) -> str:
    classes = tag.get("class") or []
    if classes:
        return f"{tag.name}." + ".".join(classes[:3])
    return tag.name


def candidate_selectors(html: str) -> dict[str, list[tuple[str, int]]]:
    soup = BeautifulSoup(html, "html.parser")
    result: dict[str, list[tuple[str, int]]] = {}
    for field, terms in KEYWORDS.items():
        counts: Counter[str] = Counter()
        for tag in soup.find_all(True):
            tag_id = tag.get("id")
            if isinstance(tag_id, list):
                tag_id = " ".join(tag_id)
            joined = " ".join((tag.get("class") or [])) + " " + (tag_id or "")
            low = joined.lower()
            if any(t in low for t in terms):
                counts[_selector_for(tag)] += 1
        result[field] = counts.most_common(10)
    return result
