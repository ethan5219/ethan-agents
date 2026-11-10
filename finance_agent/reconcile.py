"""Reconciliation checks. If any check fails, the run aborts and nothing is written.

These are the guardrails that make the agent trustworthy: the LLM never touches amounts,
and amounts are proven to tie out to the statement before anything is saved.
"""

from __future__ import annotations

from finance_agent.models import BankStatement, CardStatement

TOLERANCE = 0.005


def reconcile_card(stmt: CardStatement) -> list[str]:
    """Sum of parsed charges must equal the 'New Charges' printed on the statement."""
    issues: list[str] = []
    charges = round(sum(e.amount for e in stmt.entries if e.amount > 0), 2)
    if abs(charges - stmt.new_charges) > TOLERANCE:
        issues.append(
            f"Card {stmt.statement}: parsed charges {charges:,.2f} != "
            f"New Charges {stmt.new_charges:,.2f} (diff {charges - stmt.new_charges:+,.2f})"
        )
    if not stmt.entries:
        issues.append(f"Card {stmt.statement}: no transactions parsed")
    return issues


def reconcile_bank(stmt: BankStatement) -> list[str]:
    """TODO(Ethan): Task 4 in docs/TASKS.md.

    Checks to implement:
    1. Walk entries in order: prev_balance + deposit - withdrawal == entry.balance
       (when a balance is printed on that line). Report the first line that breaks.
    2. opening + sum(deposits) - sum(withdrawals) == closing.
    Return a list of human-readable issue strings, empty when everything ties out.
    """
    raise NotImplementedError("Task 4")


def check_payme_continuity() -> list[str]:
    """v2 (PayMe): every bank 'TO PAYME' top-up must appear in PayMe history."""
    raise NotImplementedError("v2")
