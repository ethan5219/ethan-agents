"""Spec for the categoriser. The skipped tests define 'done' for Task 5:
remove each @pytest.mark.skip as you implement, until all pass."""

import pytest

from core.audit import AuditLog
from core.hitl import Decision, ScriptedApprover
from core.llm import FakeLLM, Suggestion
from finance_agent.categorise import Categoriser
from finance_agent.parsers.boc_card import parse_boc_card
from finance_agent.rules import RuleBook

TASK5 = pytest.mark.skip(reason="Task 5: implement Categoriser._llm_then_human")


def make(rules_path, llm_answers, decisions, threshold=0.85):
    audit = AuditLog(None)
    llm = FakeLLM(llm_answers, audit)
    approver = ScriptedApprover(decisions)
    cat = Categoriser(RuleBook.load(rules_path), llm, approver, audit, threshold)
    return cat, llm, approver, audit


def test_rules_handle_known_merchants_without_llm(boc_text, rules_path):
    entries = [e for e in parse_boc_card(boc_text).entries if "KPAY" in e.desc or e.octopus]
    cat, llm, _, _ = make(rules_path, {}, [])
    stats = cat.categorise_card(entries)
    assert llm.calls == []
    assert stats.count("rule") == 1 and stats.count("octopus") == 1
    assert stats.llm_needed_rate == 0.0


@TASK5
def test_high_confidence_llm_used_directly(boc_text, rules_path):
    entries = [e for e in parse_boc_card(boc_text).entries if "CATHAY" in e.desc]
    cat, llm, approver, _ = make(
        rules_path, {"CATHAY": Suggestion(category="Travel", confidence=0.95, reason="airline")}, []
    )
    stats = cat.categorise_card(entries)
    assert entries[0].category == "Travel"
    assert stats.count("llm") == 1 and approver.asked == []


@TASK5
def test_low_confidence_goes_to_human_and_becomes_a_rule(boc_text, rules_path):
    entries = [e for e in parse_boc_card(boc_text).entries if "MYSTERY" in e.desc]
    cat, _, approver, audit = make(
        rules_path,
        {"MYSTERY": Suggestion(category="Shopping", confidence=0.4, reason="unclear")},
        [Decision("edit", "Gifts")],
    )
    stats = cat.categorise_card(entries)
    assert entries[0].category == "Gifts"
    assert stats.count("human") == 1
    assert cat.rules.match("MYSTERY MERCHANT LTD KOWLOON HK").category == "Gifts"
    assert any(e["kind"] == "hitl" for e in audit.events)


@TASK5
def test_skip_flags_confirm(boc_text, rules_path):
    entries = [e for e in parse_boc_card(boc_text).entries if "MYSTERY" in e.desc]
    cat, *_ = make(
        rules_path,
        {"MYSTERY": Suggestion(category="Shopping", confidence=0.4, reason="unclear")},
        [Decision("skip")],
    )
    cat.categorise_card(entries)
    assert entries[0].flag and entries[0].note.startswith("CONFIRM:")


@TASK5
def test_fps_always_asks_even_at_high_confidence_and_learns_no_rule(rules_path):
    from datetime import date

    from finance_agent.models import CardEntry

    e = CardEntry(
        date=date(2027, 1, 5), statement=date(2027, 1, 23), desc="FPS TO CHAN TAI MAN", amount=300
    )
    cat, _, approver, _ = make(
        rules_path,
        {"FPS": Suggestion(category="Food", confidence=0.99, reason="sure")},
        [Decision("approve", "Food")],
    )
    cat.categorise_card([e])
    assert len(approver.asked) == 1
    assert cat.rules.match("FPS TO CHAN TAI MAN") is None


@TASK5
def test_llm_never_sees_unredacted_numbers(rules_path):
    from datetime import date

    from finance_agent.models import CardEntry

    e = CardEntry(
        date=date(2027, 1, 5),
        statement=date(2027, 1, 23),
        desc="TRANSFER REF 012-345-678901",
        amount=50,
    )
    cat, llm, *_ = make(
        rules_path, {"TRANSFER": Suggestion(category="Bills", confidence=0.95, reason="x")}, []
    )
    cat.categorise_card([e])
    assert "678901" not in llm.calls[0]
