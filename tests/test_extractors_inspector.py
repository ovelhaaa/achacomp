from __future__ import annotations

from pathlib import Path

from component_radar.extractors import get_extractor
from component_radar.inspector import candidate_selectors


def test_generic_extractor_reads_price_and_relative_link():
    html = Path("tests/fixtures/generic_store_sample.html").read_text(encoding="utf-8")
    items = get_extractor("generic").extract(html, "https://x", "https://x.test", "CA3080")
    assert items
    assert items[0].price == "R$ 18,50"
    assert items[0].link == "https://x.test/p/ca3080"


def test_eletronica_castro_extractor_fixture():
    html = Path("tests/fixtures/eletronica_castro_sample.html").read_text(encoding="utf-8")
    items = get_extractor("eletronica_castro").extract(html, "https://x", "https://loja.test", "LM308")
    assert len(items) == 1
    assert items[0].title == "LM308N DIP-8"
    assert items[0].availability == "disponível"


def test_inspector_handles_missing_candidates():
    candidates = candidate_selectors("<html><body><p>sem classes</p></body></html>")
    assert "title" in candidates
    assert isinstance(candidates["title"], list)
