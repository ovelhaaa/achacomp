from __future__ import annotations

import argparse
from pathlib import Path

import requests

from .config import AppConfig, STORES_FILE, load_yaml
from .extractors import get_extractor
from .inspector import candidate_selectors
from .report import generate_report
from .scraper import _fetch, _store_search_url, run_scan
from .storage import save_latest, update_history


def cmd_scan() -> None:
    items = run_scan()
    scan_time = items[0]["scan_datetime"] if items else ""
    items = update_history(items, scan_time)
    save_latest(items)
    print(f"scan finalizado: {len(items)} achados")


def cmd_report() -> None:
    path = generate_report()
    print(f"relatório gerado em {path}")


def cmd_inspect_store(store_id: str, term: str) -> None:
    cfg = AppConfig()
    stores = load_yaml(STORES_FILE).get("stores", [])
    store = next((s for s in stores if s.get("id") == store_id), None)
    if not store:
        raise SystemExit(f"loja não encontrada: {store_id}")
    url = _store_search_url(store, term)
    session = requests.Session()
    session.headers.update({"User-Agent": cfg.user_agent})
    html = _fetch(session, url, cfg)

    debug_path = Path("data/debug")
    debug_path.mkdir(parents=True, exist_ok=True)
    dump_file = debug_path / f"{store_id}_{term}.html"
    dump_file.write_text(html, encoding="utf-8")

    base_url = store.get("base_url", url)
    specific = get_extractor(store.get("extractor", "generic")).extract(html, url, base_url, term)
    generic = get_extractor("generic").extract(html, url, base_url, term)

    print(f"store: {store_id}")
    print(f"specific: {len(specific)}")
    print(f"generic: {len(generic)}")
    print("top titles:")
    for p in specific[:10]:
        print(f"- {p.title}")

    candidates = candidate_selectors(html)
    for field, sels in candidates.items():
        print(f"Selector candidates for {field}:")
        if not sels:
            print("- none")
        for sel, n in sels:
            print(f"- {sel}: {n} matches")


def main() -> None:
    parser = argparse.ArgumentParser(prog="component-radar")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("scan")
    sub.add_parser("report")
    sub.add_parser("all")
    inspect = sub.add_parser("inspect-store")
    inspect.add_argument("--store", required=True)
    inspect.add_argument("--term", required=True)
    args = parser.parse_args()
    if args.command == "scan":
        cmd_scan()
    elif args.command == "report":
        cmd_report()
    elif args.command == "all":
        cmd_scan()
        cmd_report()
    else:
        cmd_inspect_store(args.store, args.term)


if __name__ == "__main__":
    main()
