# Task 1: Check the BOC parser against real statements

Written 2026-11-14. Task 1 proves `parse_boc_card` works on real BOC statements, not just the synthetic fixture. The regexes in `finance_agent/parsers/boc_card.py` were written against a documented format and have never seen a real PDF.

Budget: TASKS.md says 2 h. Plan for 3 to 4 h. Regex debugging on real PDFs always takes longer than expected.

## Tracker: Task 1

Tick each step when its check passes.

- [ ] Step 0: Prerequisites (Task 0 Step 5 merged, 3 PDFs in place)
- [ ] Step 1: Branch
- [ ] Step 2: Read the raw text before writing any code
- [ ] Step 3: Write `scripts/check_parser.py` and prove it on the fixture
- [ ] Step 4: Statement 1 reconciles to 0
- [ ] Step 5: Every parser fix has a synthetic line and a test
- [ ] Step 6: Statements 2 and 3 (incl. January) reconcile to 0
- [ ] Step 7: Lint, PR, merge
- [ ] Step 8: Dev log line, tick this tracker

Done when: 3 real statements print `Issues: none` and exit code 0, and every fix is covered by a synthetic test in CI.

## Privacy rules for this task

This is the first task that touches real data. Three rules:

1. Real PDFs and any text dumps live in `C:\Users\Ethan\finance-private\`, never in the repo. `*.pdf` is git-ignored, `*.txt` is NOT. A text dump inside the repo would get committed.
2. Do not paste raw statement text into Claude Code. It contains your card number, name, address and every merchant. When asking for regex help, paste one line with the merchant and amount changed by hand, keeping the exact spacing and shape.
3. The script prints to the terminal only. It writes nothing.

## The steps

All commands run in PowerShell from `C:\Users\Ethan\ethan-agents` unless stated.

### Step 0: Prerequisites

Task 1 needs Task 0 Step 5 (private folder and `.env`) finished first. Then pick 3 BOC statements: 2 recent ones and 1 January statement (that tests the December-line-goes-to-last-year logic). Name them by statement month.

```powershell
Get-ChildItem C:\Users\Ethan\finance-private\statements\boc
mkdir C:\Users\Ethan\finance-private\debug
git status
```

Check: 3 PDFs listed, e.g. `boc-2026-01.pdf`, `boc-2026-09.pdf`, `boc-2026-10.pdf`. `git status` shows nothing from the private folder.

### Step 1: Branch

```powershell
git switch main
git pull
git switch -c task-1-check-parser
```

Check: `git branch --show-current` prints `task-1-check-parser`.

### Step 2: Read the raw text before writing any code

See what `pdfplumber` actually gives you before trusting any regex. Dump one statement to the debug folder (outside the repo):

```powershell
uv run python -c "from pathlib import Path; from finance_agent.parsers.pdf_text import pdf_to_text; print(pdf_to_text(Path(r'C:\Users\Ethan\finance-private\statements\boc\boc-2026-10.pdf')))" > C:\Users\Ethan\finance-private\debug\boc-2026-10.txt
notepad C:\Users\Ethan\finance-private\debug\boc-2026-10.txt
```

Open `fixtures/boc_card_synthetic.txt` next to it and answer these questions. Each "no" is a likely bug.

| # | Question | Code that depends on it |
| --- | --- | --- |
| 1 | Is the column order POST then TRANS? If the header says TRANS DATE first, the parser reads the wrong date | `LINE_RE` groups `post`, `txn` |
| 2 | Are dates `24/09`, `24SEP` or `SEP24`? Anything else (`24 SEP`, `24-09`) is missed silently | `DATE_TOKEN` |
| 3 | Is it `Statement Date : 23/10/2026`? A format like `23 OCT 2026` raises `ParseError` | `STATEMENT_DATE_RE` |
| 4 | Is the label exactly `New Charges`? Could be `New Purchases`, `Total New Charges`, or Chinese only | `NEW_CHARGES_RE` |
| 5 | Is a credit written `58.00 CR`, `58.00CR` or `-58.00`? The minus form is missed | `(?P<cr>CR)?` |
| 6 | Do foreign-currency lines put `USD 26.90` on the same line or the next line? | `desc` lazy match, amount must be last |
| 7 | Is there a page carry-forward line like `BALANCE C/F`? It is not in `SKIP`, so it would be counted as a charge | `SKIP` |
| 8 | Is there a supplementary card section with its own subtotal? | `New Charges` may only cover one card |
| 9 | Do interest, annual fee or late charge lines exist? They count towards New Charges | Must be parsed, not skipped |

Check: you have written answers to all 9. Note the "no" answers in the Problems table below before you touch any code.

### Step 3: Write `scripts/check_parser.py`

Goal: one command that runs the full deterministic pipeline on one statement and tells you if it ties out.

```
pdf -> pdf_to_text -> parse_boc_card -> reconcile_card -> print entries, summary, issues, unmatched lines
```

Skeleton. Fill in the TODOs yourself:

```python
"""Task 1: check the BOC parser against a real statement. Prints only, writes nothing."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from finance_agent.parsers.boc_card import DATE_TOKEN, LINE_RE, ParseError, parse_boc_card
from finance_agent.parsers.pdf_text import pdf_to_text
from finance_agent.reconcile import reconcile_card

# A line that STARTS with a date token is probably a transaction.
LOOKS_LIKE_TXN = re.compile(rf"^\s*{DATE_TOKEN}\s")


def load_text(path: Path) -> str:
    # TODO: .pdf -> pdf_to_text(path); .txt -> path.read_text(encoding="utf-8");
    # anything else -> raise SystemExit with a clear message
    ...


def unmatched_lines(text: str) -> list[str]:
    # TODO: lines where LOOKS_LIKE_TXN matches but LINE_RE does not
    ...


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Check the BOC parser on one statement")
    ap.add_argument("path", type=Path)
    ap.add_argument("--unmatched", action="store_true", help="show date lines the parser skipped")
    args = ap.parse_args(argv)

    text = load_text(args.path)
    try:
        stmt = parse_boc_card(text)
    except ParseError as e:
        print(f"PARSE ERROR: {e}")
        return 2

    # TODO: one row per entry: date, amount (right-aligned), octopus flag, desc
    # TODO: summary: entry count, sum of charges, New Charges, rebates
    issues = reconcile_card(stmt)
    # TODO: print each issue, or "Issues: none"
    # TODO: if args.unmatched, print unmatched_lines(text)
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
```

Why it is built this way:

- It imports `LINE_RE` and `DATE_TOKEN` from the parser instead of copying them. One source of truth: when you fix the regex, the script sees the fix.
- `.txt` support lets you run it on the synthetic fixture, so you can prove the script itself works before blaming the parser.
- `--unmatched` is the real debugging tool. A reconcile diff tells you that something is wrong; unmatched lines tell you which line.
- Exit codes `0` ok, `1` does not reconcile, `2` cannot parse. Task 6 and any future scheduled run can act on them without reading the text.
- `main(argv)` takes a list so a test can call it directly.

Add a test so CI covers the script, in `tests/test_check_parser.py`:

```python
from scripts.check_parser import main  # adjust if scripts/ is not importable, see note


def test_fixture_reconciles(fixture_path):
    assert main([str(fixture_path)]) == 0
```

Note: `scripts/` is not a package. Either add an empty `scripts/__init__.py`, or load the file with `importlib`. Look in `tests/conftest.py` for how `boc_text` finds the fixture and reuse that path.

```powershell
uv run python scripts/check_parser.py fixtures/boc_card_synthetic.txt
$LASTEXITCODE
uv run pytest
```

Check: 8 entries, `Issues: none`, exit code `0`. pytest shows one more passing test than before.

### Step 4: Statement 1 reconciles to 0

Start with the most recent non-January statement.

```powershell
uv run python scripts/check_parser.py C:\Users\Ethan\finance-private\statements\boc\boc-2026-10.pdf --unmatched
$LASTEXITCODE
```

How to read the result:

| Output | Meaning | Where to look |
| --- | --- | --- |
| `PARSE ERROR: Statement date not found` | Header format differs | `STATEMENT_DATE_RE`, Step 2 question 3 |
| `PARSE ERROR: 'New Charges' figure not found` | Label differs | `NEW_CHARGES_RE`, question 4 |
| Diff is negative | Lines missed | `--unmatched` output, `DATE_TOKEN`, `LINE_RE` |
| Diff is positive | Something counted that should not be | Carry-forward line, payment not in `SKIP`, foreign amount parsed as HKD |
| Diff exactly equals one fee or one card's subtotal | Section or fee handling | Questions 8 and 9 |
| `no transactions parsed` | `LINE_RE` matches nothing | Column order or date format |

Debug loop: change one thing in `boc_card.py`, rerun, compare the diff. Never change two regexes at once.

Check: `Issues: none`, exit code `0`. Also eyeball 5 entries against the PDF: right date (transaction date, not post date), right sign, right amount.

### Step 5: Every parser fix gets a synthetic line and a test

Do this for each bug you fixed in Step 4, ideally before the fix (red, then green):

1. Invent a line in the same shape as the real one. Fake merchant, fake amount, same spacing, same date format, same CR style.
2. Add it to `fixtures/boc_card_synthetic.txt`.
3. Update the fixture's `New Charges` header so the file still reconciles. Update `assert len(descs) == 8` in `test_skips_payment_balance_and_odd_cents` if you added a charge.
4. Add a test in `tests/test_boc_parser.py` that asserts the new line is parsed (or skipped) correctly.

```powershell
git stash push finance_agent/parsers/boc_card.py
uv run pytest tests/test_boc_parser.py
git stash pop
uv run pytest
```

Check: with the fix stashed the new test fails; with it restored everything passes. That proves the test actually guards the bug.

### Step 6: Statements 2 and 3

```powershell
uv run python scripts/check_parser.py C:\Users\Ethan\finance-private\statements\boc\boc-2026-09.pdf --unmatched
uv run python scripts/check_parser.py C:\Users\Ethan\finance-private\statements\boc\boc-2026-01.pdf --unmatched
```

On the January statement, check that every December line is dated the previous year.

Any new bug: back to Step 4 and 5 for it, then rerun all 3 statements. A fix for one can break another.

Check: all 3 print `Issues: none`, exit code `0`.

### Step 7: Lint, PR, merge

```powershell
uv run ruff check .
uv run ruff format .
uv run pytest
git status
git add scripts tests fixtures finance_agent docs/learning/task-1-check-parser.md
git status
git commit -m "Task 1: check_parser script, BOC parser fixes from real statements"
git push -u origin task-1-check-parser
gh pr create --fill
gh pr checks --watch
gh pr diff
gh pr merge --squash --delete-branch
git switch main
git pull
```

Check: `git status` before the commit lists no `.txt` dumps, no PDFs, nothing from `finance-private`. `gh pr diff` contains no real merchant names, amounts or card numbers. PR is green and merged.

### Step 8: Dev log and tracker

Add one row to `docs/ai-dev-log.md`, tick this tracker, and ship both in the next small PR (or with the Task 2 branch).

Check: the "What broke" cell names the actual regex bugs from the Problems table.

## Concepts

| Concept | What it is | Why it matters here |
| --- | --- | --- |
| Regex named groups | `(?P<amount>...)` lets code read `lm["amount"]` instead of a group number | The parser reads `post`, `txn`, `desc`, `amount`, `cr` by name |
| Lazy quantifier | `.+?` matches as little as possible | `desc` stops before the last amount, so `USD 26.90` stays in the description |
| Anchors `^` `$` | Match must start at line start and end at line end | A trailing word after `CR` makes the whole line fail silently |
| Layout text extraction | `pdfplumber` with `layout=True` keeps columns aligned with spaces | Regex depends on that spacing; a different extractor would break it |
| Reconciliation as a test oracle | The bank prints the correct total; your parsed total must match | You don't need to know which line is wrong to know the parser is wrong |
| Silent failure | A line that doesn't match is skipped without an error | That's why `--unmatched` exists, and why reconcile must run every time |
| Exit codes | `0` ok, non-zero failed; `$LASTEXITCODE` in PowerShell | Scripts and schedulers act on them without parsing text |
| Synthetic fixture | Made-up data in the real format | Public repo can test real-world shapes without real data |
| Regression test | A test written for a specific bug you hit | That bug can never come back unnoticed |
| Red, then green | Watch the test fail without the fix, then pass with it | A test that never failed proves nothing |
| `if __name__ == "__main__"` | Runs `main()` only when the file is executed, not imported | The test can import `main` without running the script |

## Problems hit and fixes

Fill in as you go. These become the "what broke" lines in `docs/ai-dev-log.md` and interview stories.

| Problem | Cause | Fix |
| --- | --- | --- |
| | | |

## Interview lines

| Line | Keyword |
| --- | --- |
| "Reconciliation caught my parser bugs before any data was written. The statement's own New Charges total is the oracle." | Data validation, Controls |
| "Every bug from a real statement became a synthetic fixture line and a regression test, so the public repo tests real formats with zero real data." | Test automation, Data privacy |
| "A missed regex line fails silently, so the check script lists every date-shaped line the parser skipped." | Observability, Debugging |
| "Exit codes 0, 1, 2 so a scheduler can stop a run without reading logs." | Automation, DevOps |
| "I wrote the failing test before the fix to prove the test guards the bug." | TDD |
