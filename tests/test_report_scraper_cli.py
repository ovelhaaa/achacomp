from __future__ import annotations

import json
from pathlib import Path

from component_radar.config import AppConfig
from component_radar.report import generate_report
from component_radar.scraper import run_scan


def test_report_handles_empty_fields_and_escaping(tmp_path: Path):
    latest = tmp_path / "latest.json"
    latest.write_text(
        json.dumps([
            {
                "scan_datetime": "2026-01-01T00:00:00+00:00",
                "is_new": True,
                "term": "<LM308>",
                "category": "opamp",
                "store": "Loja",
                "title": "'aspas' & <tag>",
                "price": "",
                "availability": "",
                "priority": "alta",
                "audio_use": "teste",
                "link": "",
            }
        ], ensure_ascii=False),
        encoding="utf-8",
    )
    out = tmp_path / "index.html"
    generate_report(latest, out)
    html = out.read_text(encoding="utf-8")
    assert "function esc(v)" in html
    assert "const linkCell=link?" in html


def test_run_scan_deduplicates_by_hash(monkeypatch):
    import component_radar.scraper as scraper

    monkeypatch.setattr(scraper, "load_yaml", lambda path: {"categories": {"cat": {"components": ["LM308"]}}} if "targets" in str(path) else {"stores": [{"name": "S1", "base_url": "https://x.test?q={query}", "extractor": "generic"}]})
    monkeypatch.setattr(scraper, "_fetch", lambda *args, **kwargs: "<a href='/p'>LM308N</a><a href='/p'>LM308N</a>")
    monkeypatch.setattr(scraper.time, "sleep", lambda *_: None)

    items = run_scan(AppConfig(request_interval_seconds=0, retries=0))
    assert len(items) == 1
