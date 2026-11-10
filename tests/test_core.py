from core.audit import AuditLog
from core.hitl import CliApprover, Decision, ScriptedApprover
from core.llm import FakeLLM, Suggestion
from core.redact import redact, redact_names


def test_redact_masks_card_phone_email_account():
    raw = "FPS TO 9123 4567 ref 012-345-678901 card 4000 1234 5678 9010 a@b.com"
    out = redact(raw)
    for secret in ("9123", "678901", "9010", "a@b.com"):
        assert secret not in out
    assert "FPS TO" in out


def test_redact_keeps_merchant_text():
    assert redact("KPAY*CHAN KEE CAFE HONG KONG HK") == "KPAY*CHAN KEE CAFE HONG KONG HK"


def test_redact_names():
    assert redact_names("FPS WONG SAI LING", ["Wong Sai Ling"]) == "FPS [PERSON]"


def test_audit_log_writes_jsonl_and_totals(tmp_path):
    log = AuditLog(tmp_path / "a" / "audit.jsonl")
    log.record("llm_call", cost_usd=0.001)
    log.record("llm_call", cost_usd=0.002)
    log.record("hitl", action="approve")
    assert round(log.total("cost_usd", "llm_call"), 6) == 0.003
    assert len((tmp_path / "a" / "audit.jsonl").read_text().splitlines()) == 3


def test_fake_llm_is_deterministic():
    llm = FakeLLM({"cathay": Suggestion(category="Travel", confidence=0.95, reason="airline")})
    s = llm.suggest_category("CATHAY PACIFIC", 1320, ["Food", "Travel"], [])
    assert s.category == "Travel"
    assert llm.suggest_category("???", 1, ["Food", "Travel"], []).confidence < 0.5


def test_cli_approver_edit_flow():
    answers = iter(["e", "2"])
    d = CliApprover(input_fn=lambda _: next(answers)).ask("q", "Food", ["Food", "Travel"])
    assert d == Decision("edit", "Travel")


def test_scripted_approver_fails_on_unexpected_question():
    import pytest

    with pytest.raises(AssertionError):
        ScriptedApprover([]).ask("unexpected", "Food", ["Food"])
