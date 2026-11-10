"""HSBC One statement parser. TODO(Ethan): Task 3 in docs/TASKS.md.

Spec from the original skill:
- Read the HKD Savings table line by line.
- Use the date in the reference when present (e.g. 06SEP), else the posting date.
- Capture deposit, withdrawal and the printed running balance on each line.
- Opening balance = "B/F" line, closing balance = last running balance.
- Do NOT categorise here. Parsing only. Categorisation happens in categorise.py.

Acceptance: tests/test_hsbc_parser.py (you write it) passes on a synthetic fixture,
and reconcile_bank() returns no errors for it.
"""

from __future__ import annotations

from finance_agent.models import BankStatement


def parse_hsbc_bank(text: str) -> BankStatement:
    raise NotImplementedError("Task 3: implement following parsers/boc_card.py")
