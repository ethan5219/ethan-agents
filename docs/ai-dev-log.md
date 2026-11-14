# AI Dev Log

How this repo was built with Claude Code. One entry per working session.
This file is interview evidence: keep it honest, especially the "what broke" lines.

| Date       | Task     | Prompt / approach                                         | What worked                           | What broke / what I changed                                                              |
| ---------- | -------- | --------------------------------------------------------- | ------------------------------------- | ---------------------------------------------------------------------------------------- |
| 2026-11-09 | Scaffold | Scaffold, core/, BOC parser + tests generated with Claude | Test-first spec for categoriser       | Parser regex unverified against a real statement (Task 1)                                |
| 2026-11-14 | Task 0   | Repo, CI, ruleset, private folder, task panel             | Ruleset blocked a direct push to main | Committed on main by mistake; moved the commit to a branch and reset main, no force push |
