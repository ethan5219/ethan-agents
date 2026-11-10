"""`finance run 2026-10`: the end-to-end monthly run.

TODO(Ethan): Task 6 wires these steps together. The order matters:
  1. Find new statements in FINANCE_DATA_DIR/statements (not yet in finance_data.json)
  2. Parse            (parsers/)          deterministic
  3. Reconcile        (reconcile.py)      abort on any issue, write nothing
  4. Categorise       (categorise.py)     rules -> LLM -> human
  5. Show a diff of what will be added, ask approver.confirm()
  6. Append to finance_data.json, save rules.yaml
  7. Run the private workbook builder (build_finance.py) as a subprocess
  8. Print the report: counts by layer, llm_needed_rate, LLM cost, CONFIRM items
"""

from __future__ import annotations

import argparse


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="finance")
    sub = parser.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run", help="Process new statements for a month")
    run.add_argument("month", help="YYYY-MM")
    run.add_argument("--dry-run", action="store_true", help="Parse and check, write nothing")
    args = parser.parse_args(argv)

    if args.cmd == "run":
        raise SystemExit("Not wired yet: see Task 6 in docs/TASKS.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
