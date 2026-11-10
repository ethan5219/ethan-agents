"""All paths to private data come from env vars. Nothing private lives in the repo."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    data_dir: Path
    model: str
    confidence_threshold: float

    @property
    def rules_path(self) -> Path:
        return self.data_dir / "rules.yaml"

    @property
    def data_json(self) -> Path:
        return self.data_dir / "finance_data.json"

    @property
    def audit_path(self) -> Path:
        return self.data_dir / "audit" / "audit.jsonl"

    @classmethod
    def from_env(cls) -> Config:
        raw = os.environ.get("FINANCE_DATA_DIR")
        if not raw:
            raise SystemExit("FINANCE_DATA_DIR is not set. See .env.example.")
        return cls(
            data_dir=Path(raw).expanduser(),
            model=os.environ.get("FINANCE_MODEL", "claude-haiku-5-5"),
            confidence_threshold=float(os.environ.get("FINANCE_CONFIDENCE_THRESHOLD", "0.85")),
        )
