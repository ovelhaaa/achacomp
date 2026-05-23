from __future__ import annotations

from decimal import Decimal, InvalidOperation
import re


_PRICE_RE = re.compile(r"(\d{1,3}(?:\.\d{3})*,\d{2}|\d+,\d{2})")


def parse_brl_price(text: str | None) -> Decimal | None:
    if not text:
        return None
    cleaned = " ".join(str(text).split())
    match = _PRICE_RE.search(cleaned)
    if not match:
        return None
    number = match.group(1).replace(".", "").replace(",", ".")
    try:
        return Decimal(number)
    except InvalidOperation:
        return None
