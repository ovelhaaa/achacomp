from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import importlib.util
import re


@dataclass(frozen=True)
class AppConfig:
    request_interval_seconds: float = float(__import__("os").environ.get("COMPONENT_RADAR_INTERVAL","1.5"))
    timeout_seconds: int = 15
    retries: int = 2
    backoff_seconds: float = 0.8
    user_agent: str = "component-radar-br/0.1 (+https://github.com/) contato-responsavel"


ROOT = Path(__file__).resolve().parents[1]
TARGETS_FILE = ROOT / "targets.yaml"
STORES_FILE = ROOT / "stores.yaml"
DATA_DIR = ROOT / "data"
PUBLIC_DIR = ROOT / "public"
LATEST_JSON = DATA_DIR / "latest.json"
LATEST_CSV = DATA_DIR / "latest.csv"
SEEN_JSON = DATA_DIR / "seen.json"


def _mini_yaml(text: str) -> dict[str, Any]:
    lines = [ln.rstrip() for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#")]
    if lines and lines[0].startswith("stores:"):
        stores = []
        cur = None
        for ln in lines[1:]:
            if ln.strip().startswith("- "):
                if cur:
                    stores.append(cur)
                cur = {}
                continue
            m = re.match(r"\s*([a-zA-Z_]+):\s*\"?(.*?)\"?$", ln)
            if m and cur is not None:
                cur[m.group(1)] = m.group(2)
        if cur:
            stores.append(cur)
        return {"stores": stores}
    # targets parser
    out: dict[str, Any] = {"categories": {}}
    current_cat = None
    in_components = False
    for ln in lines[1:]:
        if re.match(r"^\s{2}[a-z_]+:", ln):
            current_cat = ln.strip().rstrip(":")
            out["categories"][current_cat] = {"audio_use": "", "components": []}
            in_components = False
        elif "audio_use:" in ln and current_cat:
            out["categories"][current_cat]["audio_use"] = ln.split(":", 1)[1].strip().strip('"')
        elif "components:" in ln:
            in_components = True
        elif in_components and ln.strip().startswith("-") and current_cat:
            out["categories"][current_cat]["components"].append(ln.split("-", 1)[1].strip())
    return out


def load_yaml(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if importlib.util.find_spec("yaml"):
        import yaml
        return yaml.safe_load(text) or {}
    return _mini_yaml(text)
