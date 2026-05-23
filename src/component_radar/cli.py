from __future__ import annotations

import argparse
from pathlib import Path
import re

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


def _slug_term(term: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", term.strip())
    return cleaned.strip("._-") or "term"


def _fetch_html(session: requests.Session, url: str, cfg: AppConfig) -> str:
    try:
        return _fetch(session, url, cfg)
    except requests.RequestException as exc:
        raise SystemExit(f"Falha em _fetch para URL '{url}': {exc}") from exc


def _save_debug_html(html: str, store_id: str, term: str) -> Path:
    debug_path = Path("data/debug")
    debug_path.mkdir(parents=True, exist_ok=True)
    safe_term = _slug_term(term)
    dump_file = debug_path / f"{store_id}_{safe_term}.html"
    try:
        dump_file.write_text(html, encoding="utf-8")
    except OSError as exc:
        raise SystemExit(f"Falha ao gravar dump_file '{dump_file}': {exc}") from exc
    return dump_file


def _print_inspection_results(store_id: str, specific, generic, candidates, term: str) -> None:
    print(f"store: {store_id}")
    print(f"term: {term}")
    print(f"specific: {len(specific)}")
    print(f"generic: {len(generic)}")
    print("top titles:")
    for p in specific[:10]:
        print(f"- {p.title}")
    for field, sels in candidates.items():
        print(f"Selector candidates for {field}:")
        if not sels:
            print("- none")
        for sel, n in sels:
            print(f"- {sel}: {n} matches")


def cmd_inspect_store(store_id: str, term: str) -> None:
    cfg = AppConfig()
    stores = load_yaml(STORES_FILE).get("stores", [])
    store = next((s for s in stores if s.get("id") == store_id), None)
    if not store:
        raise SystemExit(f"loja não encontrada: {store_id}")
    url = _store_search_url(store, term)
    session = requests.Session()
    session.headers.update({"User-Agent": cfg.user_agent})
    html = _fetch_html(session, url, cfg)
    _save_debug_html(html, store_id, term)

    base_url = store.get("base_url", url)
    try:
        specific = get_extractor(store.get("extractor", "generic")).extract(html, url, base_url, term)
        generic = get_extractor("generic").extract(html, url, base_url, term)
    except Exception as exc:
        raise SystemExit(f"Falha em extractor.extract para store '{store_id}': {exc}") from exc

    candidates = candidate_selectors(html)
    _print_inspection_results(store_id, specific, generic, candidates, term)


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
    elif args.command == "inspect-store":
        cmd_inspect_store(args.store, args.term)
    else:
        parser.print_help()
        raise SystemExit(f"comando desconhecido: {args.command}")


if __name__ == "__main__":
    main()
