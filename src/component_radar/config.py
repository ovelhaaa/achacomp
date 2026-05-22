from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class AppConfig:
    request_interval_seconds: float = 1.5
    timeout_seconds: int = 15
    retries: int = 2
    backoff_seconds: float = 0.8
    user_agent: str = "component-radar-br/0.1 (+https://github.com/) contato-responsavel"


ROOT = Path(__file__).resolve().parents[2]
TARGETS_FILE = ROOT / "targets.yaml"
STORES_FILE = ROOT / "stores.yaml"
DATA_DIR = ROOT / "data"
PUBLIC_DIR = ROOT / "public"
LATEST_JSON = DATA_DIR / "latest.json"
LATEST_CSV = DATA_DIR / "latest.csv"
SEEN_JSON = DATA_DIR / "seen.json"


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}
