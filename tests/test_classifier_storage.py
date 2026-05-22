from component_radar.classifier import classify_priority
from component_radar.storage import stable_hash, update_history


def test_priority_levels():
    assert classify_priority("LM308N") == "muito alta"
    assert classify_priority("2SK117") == "alta"
    assert classify_priority("CD4066") == "média"
    assert classify_priority("LM301") == "baixa"


def test_stable_hash_consistency():
    item = {"term": "LM308", "store": "Loja", "link": "http://x", "title": "LM308N"}
    assert stable_hash(item) == stable_hash(item)


def test_seen_history_update(tmp_path):
    seen_file = tmp_path / "seen.json"
    item = {"hash": "abc", "term": "LM308", "title": "LM308N", "store": "Loja"}
    out1 = update_history([item.copy()], "2026-01-01T00:00:00+00:00", seen_file)
    assert out1[0]["is_new"] is True
    out2 = update_history([item.copy()], "2026-01-02T00:00:00+00:00", seen_file)
    assert out2[0]["is_new"] is False
    assert out2[0]["first_seen"] == "2026-01-01T00:00:00+00:00"
    assert out2[0]["last_seen"] == "2026-01-02T00:00:00+00:00"
