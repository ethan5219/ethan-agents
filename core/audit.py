"""Append-only JSONL audit log. Every LLM call and every human decision is recorded.

Why: if a number in the workbook is wrong, you can trace which model call or which
approval produced it, and what it cost.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class AuditLog:
    def __init__(self, path: Path | None) -> None:
        # path=None means "don't write to disk" (used in tests)
        self.path = path
        self.events: list[dict[str, Any]] = []

    def record(self, kind: str, **fields: Any) -> dict[str, Any]:
        event = {"ts": datetime.now(UTC).isoformat(timespec="seconds"), "kind": kind, **fields}
        self.events.append(event)
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        return event

    def total(self, field: str, kind: str | None = None) -> float:
        return sum(float(e.get(field, 0)) for e in self.events if kind is None or e["kind"] == kind)
