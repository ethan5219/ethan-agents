"""Human-in-the-loop: the agent pauses and asks a person before risky or uncertain steps.

Two implementations share one interface:
- CliApprover: real terminal prompts
- ScriptedApprover: pre-set answers, so tests never block on input()
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal, Protocol

Action = Literal["approve", "edit", "skip"]


@dataclass(frozen=True)
class Decision:
    action: Action
    value: str | None = None  # the edited value when action == "edit"


class Approver(Protocol):
    def ask(self, question: str, proposed: str, choices: list[str]) -> Decision: ...

    def confirm(self, message: str) -> bool: ...


class CliApprover:
    def __init__(self, input_fn: Callable[[str], str] = input) -> None:
        self._input = input_fn

    def ask(self, question: str, proposed: str, choices: list[str]) -> Decision:
        print(f"\n{question}\n  proposed: {proposed}")
        while True:
            raw = self._input("  [a]pprove / [e]dit / [s]kip > ").strip().lower()
            if raw in ("a", "approve", ""):
                return Decision("approve", proposed)
            if raw in ("s", "skip"):
                return Decision("skip")
            if raw in ("e", "edit"):
                for i, c in enumerate(choices, 1):
                    print(f"    {i:>2}. {c}")
                pick = self._input("  number > ").strip()
                if pick.isdigit() and 1 <= int(pick) <= len(choices):
                    return Decision("edit", choices[int(pick) - 1])
            print("  invalid input, try again")

    def confirm(self, message: str) -> bool:
        return self._input(f"\n{message} [y/N] > ").strip().lower() in ("y", "yes")


class ScriptedApprover:
    """Returns pre-set decisions in order. Raises if the agent asks more than expected."""

    def __init__(self, decisions: list[Decision], confirm_answer: bool = True) -> None:
        self._decisions = list(decisions)
        self._confirm_answer = confirm_answer
        self.asked: list[str] = []

    def ask(self, question: str, proposed: str, choices: list[str]) -> Decision:
        self.asked.append(question)
        if not self._decisions:
            raise AssertionError(f"Unexpected approval request: {question}")
        return self._decisions.pop(0)

    def confirm(self, message: str) -> bool:
        self.asked.append(message)
        return self._confirm_answer
