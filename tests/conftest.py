from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def boc_text() -> str:
    return (FIXTURES / "boc_card_synthetic.txt").read_text(encoding="utf-8")


@pytest.fixture
def rules_path() -> Path:
    return FIXTURES / "rules.example.yaml"
