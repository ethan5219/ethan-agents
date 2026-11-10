"""LLM client. One narrow job: suggest a category for a transaction it has never seen.

Design choices worth explaining in an interview:
- Structured output via a forced tool call, so the reply is always JSON matching a schema.
- The category must come from a fixed list (enum), so the model cannot invent one.
- Every call is written to the audit log with token counts and cost.
- A FakeLLM with the same interface lets tests run with no API key and no network.
"""

from __future__ import annotations

import os
from typing import Protocol

from pydantic import BaseModel, Field

from core.audit import AuditLog

# USD per million tokens (input, output). PLACEHOLDER values: confirm against
# https://docs.claude.com pricing before quoting any cost figure on your CV.
PRICING: dict[str, tuple[float, float]] = {
    "claude-haiku-5-5": (1.0, 5.0),
    "claude-sonnet-5-5": (3.0, 15.0),
}


class Suggestion(BaseModel):
    category: str
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str


class LLMClient(Protocol):
    def suggest_category(
        self, description: str, amount: float, categories: list[str], hints: list[str]
    ) -> Suggestion: ...


SYSTEM_PROMPT = """You categorise one personal-finance transaction for a Hong Kong user.
Amounts are HKD. Pick exactly one category from the allowed list.
Confidence: 0.9+ only when the merchant type is unambiguous. Person-to-person payments,
cash withdrawals and unknown merchants should be below 0.6.
Use the user's own classification principles below when they apply."""


class AnthropicClient:
    def __init__(self, audit: AuditLog, model: str | None = None) -> None:
        import anthropic  # imported lazily so tests never need the package configured

        self._client = anthropic.Anthropic()
        self.model = model or os.environ.get("FINANCE_MODEL", "claude-haiku-5-5")
        self.audit = audit

    def suggest_category(
        self, description: str, amount: float, categories: list[str], hints: list[str]
    ) -> Suggestion:
        tool = {
            "name": "record_category",
            "description": "Record the category for this transaction.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "category": {"type": "string", "enum": categories},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "reason": {"type": "string", "description": "One short sentence."},
                },
                "required": ["category", "confidence", "reason"],
            },
        }
        system = SYSTEM_PROMPT + "\n\nPrinciples:\n" + "\n".join(f"- {h}" for h in hints)
        resp = self._client.messages.create(
            model=self.model,
            max_tokens=300,
            system=system,
            tools=[tool],
            tool_choice={"type": "tool", "name": "record_category"},
            messages=[
                {
                    "role": "user",
                    "content": f"Description: {description}\nAmount: {amount:.2f}",
                }
            ],
        )
        block = next(b for b in resp.content if b.type == "tool_use")
        suggestion = Suggestion.model_validate(block.input)
        in_tok, out_tok = resp.usage.input_tokens, resp.usage.output_tokens
        p_in, p_out = PRICING.get(self.model, (0.0, 0.0))
        self.audit.record(
            "llm_call",
            model=self.model,
            input_tokens=in_tok,
            output_tokens=out_tok,
            cost_usd=round((in_tok * p_in + out_tok * p_out) / 1_000_000, 6),
            description=description,  # already redacted by the caller
            category=suggestion.category,
            confidence=suggestion.confidence,
        )
        return suggestion


class FakeLLM:
    """Deterministic stand-in for tests. Maps a description substring to a Suggestion."""

    def __init__(self, answers: dict[str, Suggestion], audit: AuditLog | None = None) -> None:
        self.answers = answers
        self.audit = audit or AuditLog(None)
        self.calls: list[str] = []

    def suggest_category(
        self, description: str, amount: float, categories: list[str], hints: list[str]
    ) -> Suggestion:
        self.calls.append(description)
        for key, s in self.answers.items():
            if key.lower() in description.lower():
                self.audit.record("llm_call", model="fake", cost_usd=0.0, category=s.category)
                return s
        return Suggestion(category=categories[0], confidence=0.1, reason="fake: no match")
