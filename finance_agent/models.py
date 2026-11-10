"""Domain models. Field names match the existing finance_data.json so the agent can feed
the private workbook builder without changes."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel

CATEGORIES: list[str] = [
    # Keep in sync with CATS in the private build_finance.py (14 fixed categories).
    # TODO(Ethan): replace with your real 14 categories.
    "Food",
    "Commute",
    "Subscriptions",
    "Shopping",
    "Travel",
    "Entertainment",
    "Sports",
    "Health",
    "Education",
    "Gifts",
    "Bills",
    "Cash",
    "Fees",
    "Rebates & Refunds",
]


class CardEntry(BaseModel):
    """One BOC card line. Positive = spend, negative = credit/rebate."""

    date: date
    statement: date
    desc: str
    amount: float
    category: str | None = None
    octopus: bool = False
    flag: bool = False
    note: str | None = None


class CardStatement(BaseModel):
    statement: date
    new_charges: float  # "New Charges" figure printed on the statement
    rebates: float  # sum of rebate credits (positive number)
    entries: list[CardEntry]


BankType = Literal["Income", "Spending", "Transfer", "Reimbursement"]


class BankEntry(BaseModel):
    date: date
    statement: date
    desc: str
    deposit: float = 0.0
    withdrawal: float = 0.0
    balance: float | None = None  # running balance as printed, used for reconciliation
    type: BankType | None = None
    category: str | None = None
    flag: bool = False
    note: str | None = None


class BankStatement(BaseModel):
    statement: date
    opening: float  # B/F balance
    closing: float
    entries: list[BankEntry]
