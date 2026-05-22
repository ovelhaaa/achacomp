from __future__ import annotations

import argparse

from .report import generate_report
from .scraper import run_scan
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


def main() -> None:
    parser = argparse.ArgumentParser(prog="component-radar")
    parser.add_argument("command", choices=["scan", "report", "all"])
    args = parser.parse_args()
    if args.command == "scan":
        cmd_scan()
    elif args.command == "report":
        cmd_report()
    else:
        cmd_scan()
        cmd_report()


if __name__ == "__main__":
    main()
