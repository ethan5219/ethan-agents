"""BOC Visa statement parser (reference implementation: copy this pattern for HSBC).

Rules from the original skill:
- Each transaction line: post date, transaction date, description, amount; "CR" = credit.
- Use the TRANSACTION date.
- Skip PAYMENT THANK YOU, BALANCE B/F, ODD CENTS.
- OCTOPUS AUTO ADDING VALUE -> octopus=True, no category (builder splits commute/food).
- Year is inferred from the statement date; a December line on a January statement
  belongs to the previous year.

VERIFY(Ethan): the regexes below were written against the documented format and the
synthetic fixture, not a real statement. Task 1 in docs/TASKS.md is to check them.
"""

from __future__ import annotations

import re
from datetime import date

from finance_agent.models import CardEntry, CardStatement

MONTHS = {
    m: i
    for i, m in enumerate(
        ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"], 1
    )
}

# Accepts 24/09, 24SEP or SEP24
DATE_TOKEN = r"(?:\d{2}/\d{2}|\d{2}[A-Z]{3}|[A-Z]{3}\d{2})"
LINE_RE = re.compile(
    rf"^\s*(?P<post>{DATE_TOKEN})\s+(?P<txn>{DATE_TOKEN})\s+(?P<desc>.+?)\s+"
    rf"(?P<amount>[\d,]+\.\d{{2}})\s*(?P<cr>CR)?\s*$"
)
STATEMENT_DATE_RE = re.compile(r"Statement Date\s*:?\s*(\d{2})/(\d{2})/(\d{4})", re.I)
NEW_CHARGES_RE = re.compile(r"New Charges\s*:?\s*([\d,]+\.\d{2})", re.I)

SKIP = ("PAYMENT THANK YOU", "BALANCE B/F", "ODD CENTS")
OCTOPUS = "OCTOPUS AUTO ADDING VALUE"


class ParseError(ValueError):
    pass


def _day_month(token: str) -> tuple[int, int]:
    if "/" in token:
        d, m = token.split("/")
        return int(d), int(m)
    if token[:2].isdigit():
        return int(token[:2]), MONTHS[token[2:]]
    return int(token[3:]), MONTHS[token[:3]]


def _infer_year(month: int, statement: date) -> int:
    # A transaction can't be after the statement date: if its month is later than the
    # statement month, it happened last year (December line on a January statement).
    return statement.year - 1 if month > statement.month else statement.year


def _money(s: str) -> float:
    return float(s.replace(",", ""))


def parse_boc_card(text: str) -> CardStatement:
    m = STATEMENT_DATE_RE.search(text)
    if not m:
        raise ParseError("Statement date not found")
    d, mo, y = (int(x) for x in m.groups())
    statement = date(y, mo, d)

    nc = NEW_CHARGES_RE.search(text)
    if not nc:
        raise ParseError("'New Charges' figure not found")
    new_charges = _money(nc.group(1))

    entries: list[CardEntry] = []
    for line in text.splitlines():
        lm = LINE_RE.match(line)
        if not lm:
            continue
        desc = re.sub(r"\s{2,}", " ", lm["desc"]).strip()
        if any(s in desc.upper() for s in SKIP):
            continue
        day, month = _day_month(lm["txn"])
        txn_date = date(_infer_year(month, statement), month, day)
        amount = _money(lm["amount"]) * (-1 if lm["cr"] else 1)
        if OCTOPUS in desc.upper():
            entries.append(
                CardEntry(
                    date=txn_date, statement=statement, desc=desc, amount=amount, octopus=True
                )
            )
        else:
            entries.append(CardEntry(date=txn_date, statement=statement, desc=desc, amount=amount))

    rebates = round(-sum(e.amount for e in entries if e.amount < 0), 2)
    return CardStatement(
        statement=statement, new_charges=new_charges, rebates=rebates, entries=entries
    )
