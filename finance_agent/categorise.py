"""Categorisation in three layers. Cheapest and most reliable first.

  1. Rules (rules.yaml)             -> free, deterministic
  2. LLM suggestion (redacted input) -> used directly if confidence >= threshold
  3. Human approval (HITL)           -> for low confidence or "always ask" items;
                                        approved answers become new rules

The layer that decided each item is recorded in `decided_by`, which feeds the metrics.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

from core.audit import AuditLog
from core.hitl import Approver
from core.llm import LLMClient
from finance_agent.models import CATEGORIES, CardEntry
from finance_agent.rules import RuleBook

DecidedBy = Literal["rule", "llm", "human", "skipped", "octopus"]

# Items that must always go to a human, whatever the LLM says (from the original skill).
ALWAYS_ASK = [r"\bFPS\b", r"\bATM\b", r"7-ELEVEN.*EPS", r"\bEPS\b"]

# Your classification principles, passed to the LLM as context.
HINTS = [
    "KPay merchants are Food.",
    "Every AMAZON and PAYPAL card line is Subscriptions.",
    "APPLE.COM/BILL is Subscriptions.",
    "Taobao is Shopping.",
    "Flights, overseas activities and overseas transport are Travel.",
]


@dataclass
class Outcome:
    entry: CardEntry
    decided_by: DecidedBy


@dataclass
class RunStats:
    outcomes: list[Outcome] = field(default_factory=list)

    def count(self, by: DecidedBy) -> int:
        return sum(1 for o in self.outcomes if o.decided_by == by)

    @property
    def llm_needed_rate(self) -> float:
        """Share of categorisable items the rules could NOT handle. Should fall over time."""
        relevant = [o for o in self.outcomes if o.decided_by != "octopus"]
        if not relevant:
            return 0.0
        return sum(1 for o in relevant if o.decided_by != "rule") / len(relevant)


def must_ask(desc: str) -> bool:
    return any(re.search(p, desc, flags=re.IGNORECASE) for p in ALWAYS_ASK)


class Categoriser:
    def __init__(
        self,
        rules: RuleBook,
        llm: LLMClient,
        approver: Approver,
        audit: AuditLog,
        threshold: float = 0.85,
        categories: list[str] = CATEGORIES,
    ) -> None:
        self.rules = rules
        self.llm = llm
        self.approver = approver
        self.audit = audit
        self.threshold = threshold
        self.categories = categories

    def categorise_card(self, entries: list[CardEntry]) -> RunStats:
        stats = RunStats()
        for e in entries:
            if e.octopus:
                stats.outcomes.append(Outcome(e, "octopus"))
                continue
            rule = self.rules.match(e.desc)
            if rule is not None:
                e.category = rule.category
                stats.outcomes.append(Outcome(e, "rule"))
                continue
            stats.outcomes.append(self._llm_then_human(e))
        return stats

    def _llm_then_human(self, e: CardEntry) -> Outcome:
        """TODO(Ethan): Task 5 in docs/TASKS.md. Contract:

        1. Redact e.desc with core.redact.redact() before calling self.llm.
        2. Get a Suggestion from self.llm.suggest_category(...) with HINTS.
        3. If confidence >= self.threshold and not must_ask(e.desc):
             set e.category, return Outcome(e, "llm").
        4. Otherwise ask self.approver.ask(question, suggestion.category, self.categories):
             approve / edit -> set e.category, add a rule via
               self.rules.add(pattern_for(e.desc), category), return Outcome(e, "human")
               (do NOT add a rule for must_ask items: FPS to a person is not a merchant)
             skip -> e.flag = True, e.note = "CONFIRM: ...", return Outcome(e, "skipped")
        5. Record a "hitl" event in self.audit for every human decision.

        The skipped tests in tests/test_categorise.py define "done".
        """
        raise NotImplementedError("Task 5")
