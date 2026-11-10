"""Rules: the agent's growing memory. Checked before any LLM call.

Every category you approve in the HITL step becomes a new rule, so next month the same
merchant is handled with zero LLM calls. The share of items that still need the LLM is
the headline metric of this project.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml
from pydantic import BaseModel


class Rule(BaseModel):
    pattern: str  # case-insensitive regex matched against the description
    category: str
    type: str | None = None  # bank type override, e.g. "Transfer"
    source: str = "manual"  # "manual" | "approved" (learned from HITL)

    def matches(self, desc: str) -> bool:
        return re.search(self.pattern, desc, flags=re.IGNORECASE) is not None


class RuleBook:
    def __init__(self, rules: list[Rule]) -> None:
        self.rules = rules

    def match(self, desc: str) -> Rule | None:
        # First match wins, so put specific rules above generic ones.
        return next((r for r in self.rules if r.matches(desc)), None)

    def add(self, pattern: str, category: str, type: str | None = None) -> Rule:
        rule = Rule(pattern=pattern, category=category, type=type, source="approved")
        self.rules.append(rule)
        return rule

    @classmethod
    def load(cls, path: Path) -> RuleBook:
        if not path.exists():
            return cls([])
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or []
        return cls([Rule.model_validate(r) for r in data])

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        dumped = [r.model_dump(exclude_none=True) for r in self.rules]
        path.write_text(yaml.safe_dump(dumped, sort_keys=False, allow_unicode=True), "utf-8")


def pattern_for(desc: str) -> str:
    """Turn a description into a reusable rule pattern: keep the leading merchant words,
    drop trailing location/reference noise. Example:
    'KPAY*CHAN KEE CAFE HONG KONG HK' -> 'KPAY\\*CHAN KEE CAFE'
    """
    words = re.sub(r"\s+", " ", desc.strip()).split(" ")
    noise = {"HONG", "KONG", "HK", "HKG", "KOWLOON", "KLN"}
    kept: list[str] = []
    for w in words:
        if w.upper() in noise or re.fullmatch(r"[\d/#-]+", w):
            break
        kept.append(w)
        if len(kept) == 3:
            break
    return re.escape(" ".join(kept or words[:1]))
