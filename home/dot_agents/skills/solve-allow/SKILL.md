---
name: solve-allow
description: >
  Allow one in-between command through the SolveIt Bash jail without dropping to a
  task script. Takes a literal command or a natural-language description ("frontend
  tests", "run the migration check") and adds a single narrow Bash(...) allowlist
  entry. Also the way to see what is currently allowed mid-session.
  Trigger on: "solve-allow <thing>", "allow <command>", "let me run X directly",
  "what am I allowed to run", "/solve-allow", or a request to permit a specific
  command in this repo.
---

# solve-allow

Add a single, narrow allowance to this repo's SolveIt Bash allowlist — the
in-between grain between the barebones baseline (see the `solve-baseline` skill)
and the task-script jail. Backed by the deterministic primitive `solve-allow`
(a wrapper over `~/.claude/solveit/hooks/solve_allow.py`) so every write is a safe
JSON read-modify-write with dedup.

## Commands (the primitive)

- `solve-allow list` — print the merged allowlist for the current repo (global +
  `.claude/settings.json` + `.claude/settings.local.json`). Always runnable, even
  mid-session — use it to answer "what am I allowed to run right now?".
- `solve-allow add "<glob>" [--file F]` — add `Bash(<glob>)`.
- `solve-allow remove "<glob>" [--file F]` — remove it.

Default `--file` is `.claude/settings.local.json` (local, personal, uncommitted).

## Workflow for a request

1. **Resolve the request to a concrete command.** If given a literal command, use
   it. If given a description ("frontend tests"), inspect the repo to find the real
   command — read, do not guess:
   - `package.json` `scripts`, `Gemfile`/`Rakefile`, `Makefile`, CI config.
2. **Choose the narrowest glob** that covers the intent (e.g. `npm run test:fe` or
   `vitest run *`, not `npm *`). A broad glob re-opens the jail.
3. **Show the resolved glob and confirm** with the human before writing.
4. **Add it:** `solve-allow add "<glob>"` (local by default). Use
   `--file .claude/settings.json` only if it's a shared, baseline-worthy command —
   for that, prefer the `solve-baseline` skill.
5. **Confirm** with `solve-allow list`. It's live immediately for the guard
   (bash-guard re-reads settings every call); the injected session reminder won't
   refresh until a new session.

## Notes

- One entry per intent — don't batch many broad globs.
- To *remove* an allowance, `solve-allow remove "<glob>"`.
- To reset a repo's whole baseline, use `solve-baseline`, not repeated adds.
