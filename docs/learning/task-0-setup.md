# Task 0: Repo setup, learning log and tracker

Exported from the Claude doc on 2026-11-11. Task 0 sets up the repo, CI, branch protection and the private data folder.

## Tracker: Task 0

Tick each step when its check passes.

- [x] Step 1: Run it locally
- [x] Step 2: Set personal Git identity for this repo
- [x] Step 3: First commit, push to GitHub, CI green
- [x] Step 4: Protect main (ruleset)
- [ ] Step 5: Private data folder and .env
- [ ] Step 6: First PR with a green check (Task 0 done when this passes)

After Task 0: Task 1, check the BOC parser against 3 real statements, plus write CLAUDE.md.

## The steps

All commands run in PowerShell from `C:\Users\Ethan\ethan-agents` unless stated.

### Step 1: Run it locally

```powershell
cd C:\Users\Ethan\ethan-agents
uv sync --extra dev
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Check: `23 passed, 5 skipped`, then `All checks passed!` and `24 files already formatted`.

### Step 2: Personal Git identity for this repo only

```powershell
git init
git config user.name "Ethan Cheong"
git config user.email "<id>+<username>@users.noreply.github.com"
git config user.email
git config --global user.email
```

Check: the repo prints the noreply address. Global still prints the work address, which is correct. Noreply address: GitHub, Settings, Emails, tick Keep my email address private and Block command line pushes that expose my email.

### Step 3: First commit, push, CI

```powershell
"* text=auto eol=lf" | Out-File -Encoding ascii .gitattributes
git add --renormalize .
git add -A
git status
git commit -m "Scaffold: core, BOC parser, rules, tests, CI"
gh auth status
gh auth refresh -h github.com -s workflow
gh auth setup-git
git branch -M main
gh repo create ethan-agents --public --source . --push
git push -u origin main
gh run list --limit 5
```

Check: `git status` lists no `.env`, `.venv`, `.pdf`, `.xlsx`, `rules.yaml` or `finance_data.json`. `gh run list` shows `ci` completed success.

### Step 4: Protect main

On GitHub: Settings, Rules, Rulesets, New branch ruleset.

1. Name `protect-main`, Enforcement Active, bypass list empty
2. Target branches: Include default branch
3. Tick Restrict deletions, Block force pushes
4. Tick Require a pull request before merging, required approvals 0
5. Tick Require status checks to pass, add `test`

```powershell
git commit --allow-empty -m "should be rejected"
git push
git reset --hard HEAD~1
git status
```

Check: the push is rejected, then status says up to date with `origin/main`.

### Step 5: Private data folder and .env

```powershell
mkdir C:\Users\Ethan\finance-private\statements\boc, C:\Users\Ethan\finance-private\statements\hsbc
copy .env.example .env
notepad .env
git status
git check-ignore -v .env
```

1. In `.env`, set `FINANCE_DATA_DIR=C:/Users/Ethan/finance-private`. Leave `ANTHROPIC_API_KEY` as the placeholder until Task 5.
2. Copy, do not move, `finance_data.json` from the existing pipeline folder into `finance-private`.

Check: `git status` shows nothing new, `check-ignore` points to `.gitignore`.

### Step 6: First PR

```powershell
Get-Content .gitignore -Tail 3
git switch -c task-0-ignore-obsidian
git add .gitignore
git commit -m "Ignore Obsidian vault settings"
git push -u origin task-0-ignore-obsidian
gh pr create --fill
gh pr checks --watch
gh pr merge --squash --delete-branch
git switch main
git pull
git log --oneline -3
```

The first PR is a real change, not a dummy: adding `.obsidian/` to `.gitignore` after opening the repo as an Obsidian vault. In cmd, add the line with `echo .obsidian/>> .gitignore`, then check it in PowerShell with `Get-Content .gitignore -Tail 3`. Log the session in `docs/ai-dev-log.md` in a later PR.

Check: the PR shows a green `test` check and is merged.

## Concepts learned

| Concept | What it is | Why it matters here |
| --- | --- | --- |
| uv | Python project tool: installs Python and libraries into a project sandbox (`.venv`), pins versions in `uv.lock` | Same environment on your PC and in CI. Daily commands: `uv sync`, `uv run ...` |
| git | Version control on your machine. Tracks every change, works offline | The history of the project |
| gh | GitHub from the terminal: login, create repo, PRs, watch CI | Replaces clicking through github.com |
| CI (Continuous Integration) | On every push or PR, a fresh GitHub machine runs lint, format check and tests (`.github/workflows/ci.yml`) | Broken code never reaches main. Runs on a clean machine, nobody can skip it |
| CD (Continuous Delivery) | Automatically ships changes that pass CI | Comes with the news agent: scheduled publish to Notion |
| PR (Pull Request) | Request to merge a branch into main, with a diff page, CI checks and review | Every task: branch, push, PR, green check, self-review, merge |
| Branch protection (ruleset) | GitHub rules on main: PR only, required `test` check, no force push, no delete | Enforces the workflow even on yourself |
| Run locally first | Run tests on your PC before pushing | Known-good baseline, faster feedback than waiting for CI |
| `.env` vs `.env.example` | `.env` holds real secrets and is git-ignored. `.env.example` is a template with placeholders and is committed | A leaked API key in a public repo gets scraped within minutes |
| Global vs repo Git identity | `--global` applies to every repo on the machine. Without it, only the current repo | Other repos keep the work identity, this repo uses the personal noreply address |
| GitHub noreply email | A private address GitHub gives you for commits | Public commits show their email to anyone |
| LF vs CRLF | Linux line endings vs Windows line endings. `.gitattributes` with `eol=lf` locks the repo to LF | Avoids noisy diffs and formatter complaints |
| Git LFS settings | Large file storage config Git for Windows adds by default | Harmless, not used in this project |
| `workflow` scope | GitHub permission needed to push files in `.github/workflows/` | Workflows run code on GitHub's servers, so GitHub guards them |
| Code outside OneDrive and the vault | Repo lives in `C:\Users\Ethan\ethan-agents`, private data in `C:\Users\Ethan\finance-private` | OneDrive locks break Git. A repo inside the vault's Git could push `.env` to the vault remote |
| Repo as its own Obsidian vault | Open folder as vault on the repo. Obsidian creates `.obsidian/`, which is git-ignored | Study the .md notes without putting the repo back in OneDrive or the main vault's Git. No Obsidian Git plugin here; .md edits go through PRs |
| PowerShell vs Command Prompt | A prompt starting with `PS` is PowerShell. `Add-Content` and `Get-Content` only exist in PowerShell | All project commands are written for PowerShell |
| PR number in the log | A squash-merged PR shows as one commit ending `(#1)` | Proof in the history that the change went through a PR, not a direct push |

## Problems hit and fixes

These are the "what broke" lines for `docs/ai-dev-log.md` and for interviews.

| Problem | Cause | Fix |
| --- | --- | --- |
| Repo sat inside the OneDrive Obsidian vault | Unzipped into the notes folder | Moved to `C:\Users\Ethan\ethan-agents`, deleted and rebuilt `.venv` |
| Global Git identity was a work account | Machine set up for work | Personal noreply identity set for this repo only, global left as is |
| LF will be replaced by CRLF warnings | Windows line endings vs Linux | Added `.gitattributes` with `eol=lf`, renormalized |
| Push rejected: OAuth App without `workflow` scope | Login lacked permission to push `ci.yml` | `gh auth refresh -s workflow`, `gh auth setup-git` |
| Branch was `master`, not `main` | `init.defaultBranch` never set | `git branch -M main`, then `git config --global init.defaultBranch main` |
| `gh run watch` found no runs | CI had already finished | `gh run list` to see completed runs |
| `Add-Content` is not recognized | Terminal was Command Prompt, not PowerShell | Used `echo .obsidian/>> .gitignore`, then switched to PowerShell |
| Obsidian settings could be committed | Opening the repo as a vault creates `.obsidian/` | Added `.obsidian/` to `.gitignore` through PR #1 |

## Interview lines

| Line | Keyword |
| --- | --- |
| "Every PR runs lint, format and tests in GitHub Actions. main is protected, so nothing merges unless CI passes." | CI/CD, Code Repositories / Git |
| "main is PR-only, with a required CI check, no force pushes and no deletes." | Code Repositories / Git |
| "uv with a lockfile, so my machine and CI run identical environments." | Environment Orchestration (partial) |
| "I ran the suite locally before the first push, so CI's first run was green." | DevOps hygiene |
| "Secrets live in a git-ignored .env, real data outside the repo, synthetic fixtures only in public." | AI Governance (partial) |
