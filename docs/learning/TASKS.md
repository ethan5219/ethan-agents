# finance_agent v1: build guide

Scope: BOC card + HSBC bank. IBKR and PayMe are v2.
Pace: ~8 to 10 h/week → about 4 weeks. Hard stop: if v1 isn't done by **2026-12-13**, cut scope, don't extend.

## Working rules (these ARE the Git / CI keywords, don't skip them)
1. One branch per task: `git switch -c task-3-hsbc-parser`
2. Open a PR, CI must be green, self-review the diff on GitHub before merging. Never push to main.
3. One line in `docs/ai-dev-log.md` per session. Always fill "what broke".
4. **Never commit real data.** `.gitignore` blocks `*.pdf`, `*.xlsx`, `rules.yaml`, `finance_data.json`. Before every commit: `git status` and read the list.
5. Read every line Claude Code writes before accepting it. You will be asked to explain it.

Status: ✅ done by scaffold · ⬜ yours

---

### ✅ Scaffold
`core/` (LLM client, audit, redact, HITL), models, BOC parser, card reconciliation, rules, 23 tests, CI.
**Read all of it first** (1 to 2 h). Ask Claude Code: *"Walk me through core/llm.py. Why a forced tool call instead of asking for JSON in the prompt?"* until you can explain it without notes.

### ⬜ Task 0: Repo and private data folder (1 h)
- Create GitHub repo `ethan-agents` (public), push the scaffold to `main`, then turn on branch protection: require PR + passing `ci`.
- Create `C:\Users\Ethan\finance-private\` with `statements\boc\`, `statements\hsbc\`. Copy your current `finance_data.json` in.
- `.env` from `.env.example`.
- **Done when:** a dummy PR shows CI green.

### ⬜ Task 1: Verify BOC parser on a real statement (2 h)
- Write `scripts/check_parser.py <pdf>`: pdf → text → `parse_boc_card` → `reconcile_card` → print entries + issues.
- Run on 3 real statements (one must be a January statement for the year logic).
- If lines are missed: fix `LINE_RE` / `DATE_TOKEN`, then add a **made-up line in the same shape** to `fixtures/boc_card_synthetic.txt` and a test for it.
- **Done when:** 3 real statements reconcile to 0. **Interview point:** "reconciliation caught my parser bugs before any data was written."

### ⬜ Task 2: Import your existing knowledge (2 h)
- `scripts/import_rules.py`: read `rules` from your real `finance_data.json`, write `rules.yaml` in `FINANCE_DATA_DIR`. Mark them `source: manual`.
- Replace `CATEGORIES` in `models.py` with your real 14 (must match `CATS` in `build_finance.py`).
- Move the classification principles from the old skill into `HINTS` in `categorise.py`.
- **Done when:** rules-only run on last month's real card statement shows how many items rules already cover. Write that number down: it's your baseline.

### ⬜ Task 3: HSBC parser (4 to 6 h)
- Create `fixtures/hsbc_bank_synthetic.txt` mimicking the real layout (made-up numbers).
- Implement `parse_hsbc_bank` following the BOC pattern. Write `tests/test_hsbc_parser.py` **first**.
- Then verify on real statements like Task 1.
- Claude Code prompt: *"Here is the spec in parsers/hsbc_bank.py and the pattern in parsers/boc_card.py. Write the tests first from this synthetic fixture, then the parser. Don't touch other files."*

### ⬜ Task 4: Bank reconciliation (2 h)
- Implement `reconcile_bank` per its docstring. Tests: clean statement passes, a dropped line fails, a wrong amount fails on the right line.

### ⬜ Task 5: LLM + human layer (4 to 6 h) ← the core of the story
- Implement `Categoriser._llm_then_human` per its docstring.
- Remove the `@TASK5` skips in `tests/test_categorise.py` one at a time, make each pass.
- Add `categorise_bank` (bank entries also need `type`: Income / Spending / Transfer / Reimbursement; transfers to your own name are never spending).
- **Done when:** all tests pass with `FakeLLM`. Then one manual smoke test with the real API on 5 synthetic lines; check the audit log shows tokens and cost.

### ⬜ Task 6: Wire the CLI (4 h)
- Implement the 8 steps in `cli.py`. `--dry-run` stops after step 5.
- Adapter: append entries to `finance_data.json` in its existing shape, then run your private `build_finance.py` via `subprocess`. The builder stays private.
- **Done when:** `finance run 2026-10 --dry-run` on real data prints the diff and report.

### ⬜ Task 7: Shadow run against the old skill (2 h)
- Run the new agent and the old Claude skill on the **same month**. Compare category totals.
- Every difference is either a bug (fix it) or a rule the old skill had in its head (add it).
- **Done when:** totals match. **Interview point:** this is "pilot validation before rollout", the exact OKX JD phrase.

### ⬜ Task 8: Go live + metrics (ongoing)
- From the next statement on, the agent replaces the skill for card + bank.
- After each run, add a row to the README metrics table. After 3 months you have a trend: that's the CV number.
- Add a coverage badge to the README.

---

## v2 backlog (not now)
IBKR CSV parser + NAV checks · PayMe (vision) + continuity check · Docker · MCP server exposing the finance tools · eval set of 50 labelled transactions
