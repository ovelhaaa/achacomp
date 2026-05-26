from __future__ import annotations

import argparse
from datetime import datetime, timezone

from .config import AppConfig, STORES_FILE, SUMMARY_JSON, load_yaml
from .extractors import get_extractor
from .http import HttpClient, save_no_results_html
from .inspector import candidate_selectors
from .report import generate_report
from .scraper import _store_search_url, run_scan
from .storage import save_latest, update_history


def cmd_scan() -> None:
    items, store_status = run_scan()
    scan_time = items[0]["scan_datetime"] if items else datetime.now(timezone.utc).isoformat()
    successful = {s["store_id"] for s in store_status if s.get("success")}
    items, summary = update_history(items, scan_time, successful)
    summary.update({
        "stores_total": len(store_status),
        "stores_success": sum(1 for s in store_status if s.get("success")),
        "stores_failed": sum(1 for s in store_status if not s.get("success")),
        "failed_stores": [s for s in store_status if not s.get("success")],
    })
    save_latest(items, summary)
    print(f"scan finalizado: {len(items)} achados")


def cmd_history_summary() -> None:
    if not SUMMARY_JSON.exists():
        print("summary inexistente")
        return
    import json
    s = json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))
    print(f"novos: {s.get('items_new',0)}")
    print(f"retornos: {s.get('items_returned',0)}")
    print(f"sumidos: {s.get('items_missing',0)}")
    print(f"quedas de preço: {s.get('items_price_drop',0)}")
    print(f"lojas com erro: {s.get('stores_failed',0)}")


def cmd_report() -> None:
    path = generate_report()
    print(f"relatório gerado em {path}")

# rest unchanged helpers

def _print_inspection_results(store_id: str, specific, generic, candidates, term: str, status_code: int, html_size: int) -> None:
    print(f"store: {store_id}")
    print(f"term: {term}")
    print(f"status: {status_code}")
    print(f"html_bytes: {html_size}")
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
    http_client = HttpClient(timeout=cfg.timeout_seconds, max_retries=cfg.retries, backoff_seconds=cfg.backoff_seconds, user_agent=cfg.user_agent)
    response = http_client.get(url)
    html = response.text
    base_url = store.get("base_url", url)
    specific = get_extractor(store.get("extractor", "generic")).extract(html, url, base_url, term)
    generic = get_extractor("generic").extract(html, url, base_url, term)
    if response.status_code == 200 and not specific and not generic:
        save_no_results_html(html, store_id, term)
    candidates = candidate_selectors(html)
    _print_inspection_results(store_id, specific, generic, candidates, term, response.status_code, len(response.content))


def main() -> None:
    parser = argparse.ArgumentParser(prog="component-radar")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("scan")
    sub.add_parser("report")
    sub.add_parser("all")
    sub.add_parser("history-summary")
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
    elif args.command == "history-summary":
        cmd_history_summary()
    elif args.command == "inspect-store":
        cmd_inspect_store(args.store, args.term)


if __name__ == "__main__":
    main()
