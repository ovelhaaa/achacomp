from __future__ import annotations

import re
from difflib import SequenceMatcher

_SUFFIX_PATTERN = re.compile(r"^(?P<base>[A-Z]+\d+)(?P<suffix>[A-Z]{1,3})$")
_TOKEN_PATTERN = re.compile(r"[A-Z0-9]+")


def normalize_component_token(value: str) -> str:
    s = value.upper().strip()
    s = re.sub(r"[\s\-_/]+", "", s)
    match = _SUFFIX_PATTERN.match(s)
    if match:
        return match.group("base")
    return s


def _has_strict_token(text: str, target: str) -> bool:
    tokens = _TOKEN_PATTERN.findall(text.upper())
    norm_target = normalize_component_token(target)
    for tok in tokens:
        norm_tok = normalize_component_token(tok)
        if norm_tok == norm_target:
            if tok.startswith(target.upper()) and len(tok) > len(target) and tok[len(target)].isdigit():
                continue
            return True
    return False


def _fuzzy_ratio(a: str, b: str) -> int:
    return int(100 * SequenceMatcher(None, a, b).ratio())


def is_component_match(target: str, candidate_text: str, fuzzy_threshold: int = 92) -> bool:
    target_up = target.upper()
    text = candidate_text.upper()
    if _has_strict_token(text, target_up):
        return True

    text_norm = normalize_component_token(text)
    target_norm = normalize_component_token(target_up)
    ratio = _fuzzy_ratio(target_norm, text_norm)
    if ratio < fuzzy_threshold:
        return False
    if re.search(rf"{re.escape(target_norm)}\d", text_norm):
        return False
    return True
