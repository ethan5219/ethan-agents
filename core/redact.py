"""Strip personal data before any text leaves the machine for an LLM.

Policy: the model only ever sees a merchant-style description and an amount.
Card numbers, account numbers, phone numbers, emails and reference IDs are masked.
"""

from __future__ import annotations

import re

_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    # 13-19 digit card numbers, with or without spaces/dashes
    ("CARD", re.compile(r"\b(?:\d[ -]?){12,18}\d\b")),
    # email addresses
    ("EMAIL", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")),
    # HK phone numbers: 8 digits starting 2-9, optional +852
    ("PHONE", re.compile(r"(?:\+?852[ -]?)?\b[2-9]\d{3}[ -]?\d{4}\b")),
    # account-like numbers: 3-3-6 style or long digit runs (6+)
    ("ACCT", re.compile(r"\b\d{3}-\d{3}-\d{3,6}\b|\b\d{6,}\b")),
]


def redact(text: str) -> str:
    out = text
    for label, pattern in _PATTERNS:
        out = pattern.sub(f"[{label}]", out)
    return out


def redact_names(text: str, names: list[str]) -> str:
    """Mask known personal names (e.g. family members) supplied from private config."""
    out = text
    for name in names:
        if name.strip():
            out = re.sub(re.escape(name), "[PERSON]", out, flags=re.IGNORECASE)
    return out
