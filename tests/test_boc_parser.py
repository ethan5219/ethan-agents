from datetime import date

import pytest

from finance_agent.parsers.boc_card import ParseError, _infer_year, parse_boc_card
from finance_agent.reconcile import reconcile_card


def test_statement_header(boc_text):
    s = parse_boc_card(boc_text)
    assert s.statement == date(2027, 1, 23)
    assert s.new_charges == 2468.30


def test_skips_payment_balance_and_odd_cents(boc_text):
    descs = [e.desc for e in parse_boc_card(boc_text).entries]
    assert not any("PAYMENT THANK YOU" in d for d in descs)
    assert not any("BALANCE B/F" in d for d in descs)
    assert not any("ODD CENTS" in d for d in descs)
    assert len(descs) == 8


def test_uses_transaction_date_and_infers_previous_year(boc_text):
    first = parse_boc_card(boc_text).entries[0]
    assert first.desc.startswith("KPAY*CHAN KEE CAFE")
    assert first.date == date(2026, 12, 26)  # December line on a January statement


def test_credit_is_negative_and_rebates_summed(boc_text):
    s = parse_boc_card(boc_text)
    rebate = next(e for e in s.entries if "CASHBACK" in e.desc)
    assert rebate.amount == -58.00
    assert s.rebates == 58.00


def test_octopus_flagged_without_category(boc_text):
    octo = next(e for e in parse_boc_card(boc_text).entries if e.octopus)
    assert octo.amount == 250.00
    assert octo.category is None


def test_synthetic_statement_reconciles(boc_text):
    assert reconcile_card(parse_boc_card(boc_text)) == []


def test_reconcile_catches_a_dropped_line(boc_text):
    s = parse_boc_card(boc_text)
    s.entries.pop(1)  # simulate a parser bug that loses a line
    issues = reconcile_card(s)
    assert len(issues) == 1 and "diff" in issues[0]


def test_missing_statement_date_raises():
    with pytest.raises(ParseError):
        parse_boc_card("no header here")


@pytest.mark.parametrize(
    "month,stmt,expected",
    [(12, date(2027, 1, 23), 2026), (1, date(2027, 1, 23), 2027), (6, date(2026, 6, 23), 2026)],
)
def test_infer_year(month, stmt, expected):
    assert _infer_year(month, stmt) == expected
