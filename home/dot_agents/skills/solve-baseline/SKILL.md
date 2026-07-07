---
name: solve-baseline
description: >
  Curate the SolveIt Bash allowlist for the current repo down to a barebones
  baseline of validation commands (lint, test, typecheck, db setup, server/compile)
  and strip noise. Explores the repo to discover the right commands, proposes a
  KEEP/DROP plan, and only writes to .claude/settings.json after you approve.
  Everything not on the baseline keeps going through SolveIt task scripts.
  Trigger on: "curate the allowlist", "set up baseline commands", "clean the
  permission list", "/solve-baseline", or setting up SolveIt in a new repo.
---

# solve-baseline

Curate this repo's SolveIt `permissions.allow` Bash entries down to a **barebones
baseline** — the few commands needed for smooth validation — and drop noise. The
baseline is the repo's committed validation contract; everything else stays in the
task-script jail (see [SolveIt default mode] and the `solve-allow` skill).

Backed by the deterministic primitive `solve-allow` (a thin wrapper over
`~/.claude/solveit/hooks/solve_allow.py`), so all writes are safe JSON
read-modify-write with dedup — never hand-edit the JSON.

## What counts as baseline

Only the barebones commands that establish a smooth validation loop:

- **lint** (e.g. `npm run lint`, `rubocop`, `ruff check`)
- **test** (e.g. `npm test`, `bin/rails test`, `pytest`)
- **typecheck / compile** (e.g. `npx tsc --noEmit`, `cargo check`)
- **db setup** (e.g. `bin/rails db:prepare`, `bin/rails db:test:prepare`)
- **build / server-compile** where validation needs it

Not baseline (leave for task scripts or the `solve-allow` skill): one-off scripts,
deploys, long-running servers, ad-hoc data mutation, anything destructive.

## Workflow

1. **Read the current allowlist:** run `solve-allow list` in the repo.
2. **Discover baseline commands** by inspecting the repo — read, do not guess:
   - `package.json` `scripts` (lint/test/typecheck/build)
   - `Gemfile`, `Rakefile`, `bin/`, `.rubocop.yml`
   - `tsconfig.json`, `pyproject.toml`, `Makefile`, `Cargo.toml`
   - CI config (`.github/workflows/*`, `.gitlab-ci.yml`) — the commands CI runs
     are the strongest signal for the true baseline.
3. **Propose a KEEP/DROP plan** as a table. KEEP = the minimal baseline globs (use
   narrow globs, e.g. `npm test`, not `npm *`). DROP = entries in the current
   allowlist that are noise for this repo. Cite where each KEEP came from.
4. **Get explicit approval.** Do not write anything before the human says yes.
5. **Apply** with the primitive, targeting the shared committed file:
   - add:    `solve-allow add "<glob>" --file .claude/settings.json`
   - remove: `solve-allow remove "<glob>" --file <file it lives in>`
   (drop entries from whichever settings file currently holds them —
   `.claude/settings.json` or `.claude/settings.local.json`.)
6. **Report** the final baseline (`solve-allow list`) and remind: everything else
   runs as a SolveIt task script under `.solve/tasks/`.

## Notes

- Changes take effect immediately for the guard (bash-guard re-reads settings on
  every call). The per-session injected reminder won't refresh until a new session.
- Keep globs narrow and literal — a broad glob re-opens the jail you're curating.
- Prefer `.claude/settings.json` (committed, shared) for the baseline so the whole
  team inherits the same validation contract.
