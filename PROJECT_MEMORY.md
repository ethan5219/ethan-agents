# ethan-agents: project memory (AI handoff)

Last updated: 2026-11-15. Paste this whole file into a new AI chat to give it full context. It covers what the project is, where things live, the rules, current status and what to do next.

---

## 1. Who I am and how to work with me

- I'm Ethan. HKUST Finance + Information Systems graduate. Management Trainee (IT stream, BA/PM hybrid) at ESDLife, Hong Kong, since July 2026.
- I'm building this repo myself, in Claude Code, on top of a Claude-generated scaffold. **Explain the code; don't just hand it over.** I need to be able to explain every line in an interview.
- Pace: about 8 to 10 h per week.
- Style I want from you:
  - Direct, no filler. Push back when I'm wrong, with a real argument.
  - Step-by-step PowerShell commands, each step ending with a `Check:` line (same format as `docs/learning/task-0-setup.md`).
  - Point out interview talking points and JD keywords as we go (e.g. "pilot validation before rollout", HITL, reconciliation, CI, audit trail).
  - Don't use the ` — ` dash in responses. Flag important things in bold with a ⚠️ prefix.
- I'm on Windows, PowerShell. I use Obsidian for notes (this repo is also opened as its own Obsidian vault).

---

## 2. What the project is

- Public repo: **github.com/ethan5219/ethan-agents**
- Goal: rebuild my Claude "Finance Monthly Run" skill (which updates my private Finance.xlsx from BOC card, HSBC bank, IBKR and PayMe statements) as **tested Python code**. It's a CV and interview project as much as a tool.
- Core design rule: **the LLM only does judgment (categorising). Parsing and reconciliation are deterministic code. Nothing gets written unless the totals tie out.**
- README lists two agents: `finance_agent` (v1 in progress) and `news_agent` (daily finance + tech digest to Notion, planned, not started).

### Scope
- **v1:** BOC credit card + HSBC bank only.
- **v2 backlog (not now):** IBKR CSV parser + NAV checks, PayMe (vision) + continuity check, Docker, MCP server exposing the finance tools, eval set of 50 labelled transactions.
- ⚠️ **Hard stop: if v1 isn't done by 2026-12-13, cut scope, don't extend.**

### Pipeline (`finance run 2026-10`)
1. Find new statements in `FINANCE_DATA_DIR/statements` (not yet in finance_data.json)
2. Parse (deterministic, no LLM)
3. Reconcile: running balance, top-up continuity, totals tie out. Any issue = abort, write nothing
4. Categorise: match `rules.yaml` first → unmatched lines are redacted → LLM returns category + confidence + reason → high confidence accepted; low confidence or "always ask" items go to a human (approve / edit / skip) → approved answers become new rules in `rules.yaml` (knowledge accumulation)
5. Show a diff of what will be added, ask for confirmation
6. Append to `finance_data.json`, save `rules.yaml`
7. Run the private workbook builder `build_finance.py` as a subprocess (the builder stays private, never in the repo)
8. Print report: counts by layer (rule / llm / human / skipped), llm_needed_rate, LLM cost, CONFIRM items

`--dry-run` stops after step 5. Every LLM call and human decision goes to an audit log (tokens, cost).

---

## 3. Stack

uv, Python 3.12, pytest (+ coverage), ruff (lint + format check), pdfplumber, pydantic, anthropic SDK, GitHub Actions CI.

CI (`.github/workflows/ci.yml`, workflow `ci`, job `test`) runs on every PR and on push to main: `uv sync --extra dev` → `ruff check .` → `ruff format --check .` → `pytest --cov=core --cov=finance_agent`. No API key, no network in CI (tests use `FakeLLM` / fake approver).

---

## 4. Repo layout (as of 2026-11-15)

```
core/
  llm.py        LLM client. Forced tool call (not "please return JSON") → Suggestion
                (category, confidence, reason). Has SYSTEM_PROMPT and a FakeLLM for tests.
  audit.py      AuditLog: record(kind, **fields), total(field, kind)
  redact.py     redact(text), redact_names(text, names): strip personal data before LLM
  hitl.py       Approver protocol: ask(question, proposed, choices) -> Decision, confirm(msg).
                Console approver (input()) + scripted fake for tests
finance_agent/
  models.py     pydantic models (CardEntry, CardStatement, BankStatement...), CATEGORIES
  parsers/
    pdf_text.py   PDF → text (pdfplumber)
    boc_card.py   parse_boc_card(text) -> CardStatement. Key regexes: DATE_TOKEN, LINE_RE,
                  STATEMENT_DATE_RE, NEW_CHARGES_RE. SKIP = PAYMENT THANK YOU / BALANCE B/F /
                  ODD CENTS. OCTOPUS AUTO ADDING VALUE lines flagged as octopus.
                  _infer_year handles Dec lines on a Jan statement.
    hsbc_bank.py  spec only, parse_hsbc_bank is Task 3
  reconcile.py  reconcile_card (done), reconcile_bank (Task 4), check_payme_continuity (v2).
                TOLERANCE = 0.005
  rules.py      RuleBook: match(desc), add(pattern, category); loads/saves rules.yaml
  categorise.py Categoriser(rules, llm, approver, audit, threshold=0.85).
                categorise_card: octopus → rule → _llm_then_human (Task 5 stub).
                must_ask(desc) checks ALWAYS_ASK patterns (e.g. FPS to a person). HINTS live here
  config.py     reads FINANCE_DATA_DIR etc. from .env
  cli.py        argparse `finance run YYYY-MM [--dry-run]`, not wired (Task 6)
tests/          conftest, test_boc_parser, test_categorise (5 skipped with @TASK5),
                test_core, test_rules
fixtures/       boc_card_synthetic.txt, rules.example.yaml (made-up data only)
docs/
  finance_agent.md               mermaid flow diagram
  ai-dev-log.md                  one row per session (interview evidence)
  learning/TASKS.md              the build guide (Tasks 0-8)
  learning/task-0-setup.md       Task 0 walkthrough (done)
  learning/task-1-check-parser.md  Task 1 walkthrough with tracker (not started)
  Project Management Panel.base  Obsidian TaskNotes kanban over docs/To Do list/
  To Do list/                    task notes
.env / .env.example, .gitattributes (LF line endings), .gitignore, pyproject.toml, uv.lock
```

Test baseline after scaffold: **23 passed, 5 skipped** (the @TASK5 ones).

---

## 5. Locations on my machine

- Repo: `C:\Users\Ethan\ethan-agents` (deliberately outside OneDrive and my main Obsidian vault; `.obsidian/` and `TaskNotes/` are git-ignored).
- Private data: `C:\Users\Ethan\finance-private\`
  - `finance_data.json`, `rules.yaml`, audit log, `debug\` (text dumps for Task 1)
  - `statements\` with six subfolders mirroring my original ones. **Keep all six, including empty v2 ones:** `Credit Card (BOC)`, `Credit Card (Hang Seng)`, `Credit Card (HSBC)`, `IBKR`, `PayMe screenshots`, `Saving (HSBC)`
  - Note: TASKS.md and task-1 notes still say `statements\boc\` / `statements\hsbc\`; the real folders are the six above.
- Original statements used by the old skill: `C:\Users\Ethan\OneDrive\Desktop\Personal Obsidian\Investment Finance\Statements\<same six folders>`. They were **copied, not moved**.
- Old skill's `finance_data.json`: `C:\Users\Ethan\OneDrive\Desktop\Personal Obsidian\Investment Finance\_pipeline\`

---

## 6. Git and privacy rules (non-negotiable)

- Repo commits as personal identity `user.name "ethan5219"` with the GitHub noreply email, set at **repo level**. My global git identity is my work account. ⚠️ **Never change global git config.**
- `main` is protected by ruleset `protect-main`: PR only, required status check `test`, no force push, no delete.
- Flow per task:
  ```powershell
  git switch main; git pull
  git switch -c task-N-name
  # work, git status, commit
  git push -u origin task-N-name
  gh pr create --fill
  gh pr checks --watch
  # self-review the diff on GitHub
  gh pr merge --squash --delete-branch
  ```
- ⚠️ **Never commit real data.** `.gitignore` blocks `*.pdf`, `*.xlsx`, `rules.yaml`, `finance_data.json`, `.env`. `*.txt` is NOT blocked, so text dumps must stay in `finance-private\debug\`. Run `git status` before every commit and read the list.
- Never paste raw statement text into an AI chat (card number, name, address, merchants). For regex help, paste one line with merchant and amount changed by hand, keeping exact spacing and shape.
- One line in `docs/ai-dev-log.md` per session. Always fill "what broke".
- Read every line Claude Code writes before accepting it.

---

## 7. Status (as of 2026-11-15)

Merged PRs on main (squash):
- Scaffold commit: core, BOC parser, rules, tests, CI
- #1 Ignore Obsidian vault settings
- #2 Add Task 0 learning log
- #3 Ignore TaskNotes, enforce LF line endings
- #4 task 0 finish (finance-private populated, .env, project panel, Task 1 notes, tracker ticks, dev-log line), merged 2026-11-14
- #5 Fix Git identity lines in Task 0 guide
- #7 Correct username and email in Task 0 guide

**Task 0 is complete.** Working tree clean. No `scripts/` folder and no `CLAUDE.md` yet.

Dev log so far:
| Date | Task | What broke |
|---|---|---|
| 2026-11-09 | Scaffold | Parser regex unverified against a real statement (Task 1) |
| 2026-11-14 | Task 0 | Committed on main by mistake; moved the commit to a branch and reset main, no force push |

### Known loose ends (small, fix when convenient)
- `TASKS.md` still shows Task 0 as ⬜ and says "require passing `ci`"; the actual required check is `test`.
- Docstrings in `categorise.py` and `cli.py` point to `docs/TASKS.md`; it moved to `docs/learning/TASKS.md`.
- Statement folder names in TASKS.md / task-1 notes don't match the real six folders (see section 5).

---

## 8. Next steps (in order)

1. **Write repo `CLAUDE.md`**: the git and privacy rules above, the privacy model (real data only in finance-private, redact before LLM), and "tests first, don't touch other files".
2. **Task 1: verify the BOC parser on real statements (budget 2 h, plan 3 to 4 h).**
   - Branch `task-1-check-parser`.
   - Dump raw pdfplumber text of one statement into `finance-private\debug\` and read it before writing code.
   - Write `scripts/check_parser.py <pdf>`: pdf → text → `parse_boc_card` → `reconcile_card` → print entries + issues. Writes nothing. Prove it on the synthetic fixture first.
   - Run on 3 real BOC statements, one of them a January statement (year inference).
   - If lines are missed: fix `LINE_RE` / `DATE_TOKEN`, add a made-up line of the same shape to `fixtures/boc_card_synthetic.txt`, and add a test.
   - Done when: 3 real statements print `Issues: none`, exit code 0, every fix covered by a synthetic test in CI.
   - Interview point: "reconciliation caught my parser bugs before any data was written."
3. **Task 2: import existing knowledge (2 h).** `scripts/import_rules.py` reads `rules` from the real `finance_data.json` and writes `rules.yaml` (`source: manual`). Replace `CATEGORIES` in `models.py` with my real 14 (must match `CATS` in `build_finance.py`). Move the old skill's classification principles into `HINTS`. Done when a rules-only run on last month's card statement gives the coverage number: that's the baseline.
4. **Task 3: HSBC parser (4 to 6 h).** Synthetic fixture `fixtures/hsbc_bank_synthetic.txt` first, then `tests/test_hsbc_parser.py` first, then `parse_hsbc_bank` following the BOC pattern, then verify on real statements.
5. **Task 4: bank reconciliation (2 h).** `reconcile_bank` per docstring. Tests: clean passes, dropped line fails, wrong amount fails on the right line.
6. **Task 5: LLM + human layer (4 to 6 h), the core of the story.** Implement `Categoriser._llm_then_human`:
   - redact `e.desc` → `llm.suggest_category(...)` with HINTS
   - confidence ≥ threshold and not `must_ask` → accept, Outcome "llm"
   - else ask approver: approve/edit → set category, add rule via `rules.add(pattern_for(desc), category)` (no rule for must_ask items, FPS to a person is not a merchant), Outcome "human"; skip → `flag=True`, note `CONFIRM: ...`, Outcome "skipped"
   - record a `hitl` audit event for every human decision
   - unskip the @TASK5 tests one at a time. Add `categorise_bank` (bank entries need `type`: Income / Spending / Transfer / Reimbursement; transfers to my own name are never spending). Then one manual smoke test with the real API on 5 synthetic lines; check audit log shows tokens and cost.
7. **Task 6: wire the CLI (4 h).** The 8 steps in section 2. Adapter appends to `finance_data.json` in its existing shape, then runs private `build_finance.py` via subprocess. Done when `finance run 2026-10 --dry-run` on real data prints diff and report.
8. **Task 7: shadow run (2 h).** New agent vs old skill on the same month, compare category totals. Each difference is a bug or a rule the old skill had in its head. Interview point: "pilot validation before rollout".
9. **Task 8: go live + metrics.** Agent replaces the skill for card + bank. Add a row to the README metrics table after each run (3 months = CV trend). Add a coverage badge.

---

## 9. Interview talking points collected so far

- Deterministic parsing + reconciliation gate before anything is written; LLM limited to judgment.
- Forced tool call for structured LLM output instead of prompting for JSON.
- Redaction before any LLM call; real data never in the public repo.
- Human-in-the-loop with confidence threshold, "always ask" list, and rule learning from approvals.
- Audit log with token and cost tracking; llm_needed_rate as the metric that should fall over time.
- Branch protection, PR-only flow, required CI, squash merges, honest AI dev log including mistakes (the accidental commit on main, fixed without force push).
- Shadow run against the old system = pilot validation before rollout.
