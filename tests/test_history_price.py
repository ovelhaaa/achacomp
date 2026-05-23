from decimal import Decimal

from component_radar.history import update_history
from component_radar.price import parse_brl_price


def test_parse_brl_price():
    assert parse_brl_price("R$ 12,90") == Decimal("12.90")
    assert parse_brl_price("R$12,90") == Decimal("12.90")
    assert parse_brl_price("R$ 1.234,56") == Decimal("1234.56")
    assert parse_brl_price("12,90") == Decimal("12.90")
    assert parse_brl_price("Consulte") is None
    assert parse_brl_price("") is None


def _item(price="R$ 10,00", availability="em estoque"):
    return {"hash": "a1", "term": "LM308", "category": "opamp", "store": "Loja", "store_id": "loja", "title": "LM308N", "link": "https://x", "price": price, "availability": availability, "priority": "alta", "audio_use": "sim"}


def test_history_events():
    seen = {}
    now = "2026-01-01T00:00:00+00:00"
    items, seen, summary = update_history([_item()], seen, now, {"loja"})
    assert items[0]["event"] == "new"
    items, seen, _ = update_history([_item()], seen, "2026-01-02T00:00:00+00:00", {"loja"})
    assert items[0]["event"] == "unchanged"
    items, seen, _ = update_history([_item(price="R$ 8,00")], seen, "2026-01-03T00:00:00+00:00", {"loja"})
    assert items[0]["price_drop"] is True
    assert items[0]["price_drop_significant"] is True
    items, seen, _ = update_history([_item(price="R$ 12,00")], seen, "2026-01-04T00:00:00+00:00", {"loja"})
    assert items[0]["price_increase"] is True
    items, seen, _ = update_history([_item(price="R$ 12,00", availability="indisponível")], seen, "2026-01-05T00:00:00+00:00", {"loja"})
    assert items[0]["availability_changed"] is True
    items, seen, summary = update_history([], seen, "2026-01-06T00:00:00+00:00", {"loja"})
    assert summary["items_missing"] == 1
    items, seen, _ = update_history([_item()], seen, "2026-01-07T00:00:00+00:00", {"loja"})
    assert items[0]["event"] == "returned"


def test_failed_store_not_missing():
    seen = {"a1": {"stable_id": "a1", "store_id": "loja", "status": "active", "last_event": "seen_again"}}
    _, _, summary = update_history([], seen, "2026-01-01", set())
    assert summary["items_missing"] == 0


def test_first_sighting_does_not_set_availability_changed():
    items, _, _ = update_history([_item(availability="em estoque")], {}, "2026-01-01", {"loja"})
    assert items[0]["availability_changed"] is False


def test_legacy_missing_without_store_id_when_some_store_succeeded():
    seen = {
        "legacy": {
            "stable_id": "legacy",
            "status": "active",
            "store_id": "",
            "search_term": "LM308",
            "category": "opamp",
        }
    }
    _, _, summary = update_history([], seen, "2026-01-01", {"loja"})
    assert summary["items_missing"] == 1
    ev = summary["events"][0]
    assert ev["event"] == "missing"
    assert "term" in ev and "category" in ev
