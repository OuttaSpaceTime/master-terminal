---
title: SolveIt default mode
tags: [claude-code, solveit, output-styles, hooks]
created: 2026-06-13
updated: 2026-07-30
---

# SolveIt default mode

Claude Code runs in **SolveIt mode by default** in every session — incremental, human-as-agent work with hard guardrails against agent eagerness, wired into the global `~/.claude/settings.json`. The old `claude-solve` wrapper that scoped this per-invocation has been **retired**: it's the default now, so plain `claude` is already constrained. See [Solveit Method](solveit-method.md) for the underlying philosophy.

## How it's wired

`~/.claude/settings.json` turns on the mechanisms globally:

1. **`outputStyle: "solveit"`** — the soft layer. Injects the SolveIt method into the system prompt and re-asserts it as a reminder every turn (this is what fights eager-drift over long sessions — `--append-system-prompt` injects only once and fades). Built with `keep-coding-instructions: true` so Claude keeps its engineering ability. Reinforced by a short **"SolveIt is the default mode"** section in `~/.claude/CLAUDE.md`.
2. **A `UserPromptSubmit` hook** (`solve-init.py`) — once per session (guarded by a marker in `~/.claude/solveit/state/<session_id>.solve`), adds `.solve/` to the repo's `.git/info/exclude` (so scratch and `reads.log` never dirty the tree) and injects a short reminder of how the Bash/edit guards work. There is **no `solve.md`** and no auto-created folder anymore — the human keeps any task document they want, and task scratch lives under `.solve/tasks/` created on demand.
3. **Three `PreToolUse` hooks** — the hard layer that does not drift:
   - `Write|Edit|MultiEdit` → `edit-guard.py` (line caps + two-tier commit cap)
   - `Bash` → `bash-guard.py` (strict: only task scripts + read-only search/git; specific commands can be allowlisted — see below)
   - `Read|Grep|Glob` → `log-reads.py` (logs what the agent reads; never blocks). Read-only shell searches and read-only git allowed by `bash-guard.py` are logged to the same `.solve/reads.log`.

### Output style behavior (`~/.claude/output-styles/solveit.md`)

- Human sets direction; Claude does **not** propose the next step or a plan unless asked.
- Equally for building, exploring, learning, and planning. A *step* need not be code — it can be "put a breakpoint here", "check this value", "run this command", "drive the app like this and observe", or refining a document you write yourself.
- **Probe-it is the default step shape** — hand a runnable probe (live inspection preferred: debugger, `bin/rails c`/REPL, task-script probe; reading the real source at `path:line` counts too, best when verified with a test/debugger), have the human predict the output, then reveal. Applies to building a feature too, not just understanding. Socratic and terse for design; **TDD as the primary loop** for app code (task folder is auxiliary only).
- One concrete example first; JRY before DRY; every reply ends with a verify-it-yourself handoff.
- Claude may run a verification itself but must always hand you a way to verify and tweak it.

### Hard limits (enforced by hooks)

- **≤30 added lines per edit** — a ceiling, not a target (`edit-guard.py`, `CAP`).
- **≤4 project-code edits per human turn** (`EDIT_CAP`) — one step, then hand back. The counter is reset by `solve-init.py` on every prompt; writes under `.solve/` don't count.
- **Three-tier uncommitted cap** — a checkpoint is due at **30+ *unstaged* lines** (staging what you accept lets work continue), a **warning** at 150 total, and a **hard block at 300 total** where only a real commit helps. Counts tracked diff vs HEAD plus untracked file lines in the enclosing repo. `.solve/` is git-excluded, so task scratch never counts. Either way Claude never commits: it stops and says what changed; you commit before more is written.
- **Escape valve for a deliberate multi-commit split** — `touch .solve/splitting` lifts *only* the 300 hard block (the 30-line unstaged checkpoint and the 150 warning still apply). Use it when you've built one pile on purpose and want to slice it into several commits without the cap fighting you: staging can't help there, because the total is measured vs `HEAD`, so `git add` just moves lines between the staged and dirty buckets. The first write after you drop the marker stamps that session's id into it; a later chat finds a foreign id, deletes the marker and enforces the cap again — off by default, dies with the chat. Claude is denied writes to the marker, so only you can open the valve.
- **Bash runs task scripts and read-only search/inspection** (`bash-guard.py`). A Bash command is allowed only if every segment is one of: a runner — an interpreter (`python`, `sh`, `ruby`, `node`, …), a `./path` execution, or any non-destructive runner (`bin/rails runner`, `bundle exec ruby`, `npx tsx`, `rake`, …) — invoking a file under `.solve/tasks/<X>/` that **exists**, in a folder `<X>` that also contains a `.md`. **The script path must be the last token** — no args/flags/redirects passed at run time, so a script can't be a generic command forwarder (e.g. `exec bin/rails "$@"`); bake the exact command into the file. (Piping the script's output — `… | grep x` — is fine, since the pipe splits into a separate segment.) **A runner must point at a FILE, never an inline code string** — `bin/rails runner -e "…"`, `ruby -e`, `python -c`, `sh -c "…"` (and `--eval`/`--command`) are blocked; read-only commands' own `-e`/`-c` (e.g. `grep -e`, `head -c`) are unaffected since they match earlier. A segment may instead be a **read-only search/inspection** command (`grep`, `rg`, `find`, `ls`, `cat`, `head`, `tail`, `awk`, … — no `>`/`>>` redirect, and `find` may not `-exec`/`-delete`), optionally wrapped in **read-only shell structure** (`for`/`while`/`if` loops and pipes — each inner command is still validated, so a loop hiding `rm` is still blocked); **read-only git** (`diff`, `status`, `log`, `show`, `blame`, `ls-files`, `rev-parse`, … — the dual-use `branch`/`tag`/`remote`/`stash`/`checkout`/`reset` are *not* in the allowlist); `git init` (to create a scratch repo — commits nothing); `cd`; or `mv` **within** `.solve/tasks/` (for renaming a task folder). Segments are split **quote-aware** (a `\|` inside a grep pattern or a `;` inside a commit message no longer mis-splits). Read-only search is allowed because a tool-registration bug ([#52121](https://github.com/anthropics/claude-code/issues/52121)) can drop the `Grep`/`Glob` tools entirely, leaving shell as the only way to look at code; each allowed search **and read-only git** is appended to `reads.log`. Everything else is blocked — ad-hoc one-liners that mutate, **all** repo-mutating git (`add`/`commit`/`--amend`/`checkout`/`reset`/`stash`/`apply`, in any repo), test runners (`pytest`, `python -m pytest` → wrap in a task script), and installs. Commands you explicitly allow via `permissions.allow` `Bash(...)` entries bypass all of this (see below). So everything the agent *executes against the project* is a reviewable file on disk, while *looking* stays cheap.
- **No agent commits — ever** — Claude **never commits anything**. All `git add`/`commit`/`--amend` (and other mutating git) are blocked; you commit every checkpoint and `--amend` freely. The whole philosophy is to keep changes **dirty** so you verify and commit. Only `git init` (to make a task folder its own scratch repo) and read-only git are allowed.
- **Re-running is unlimited** — running an existing task script is always allowed. Repeat work (e.g. tests) = write a descriptive script once, re-run it.

The guard hooks **fail open**: any internal error allows the tool call, so a bug never wedges a session. Since 2026-07-30 a failure is no longer silent — each hook appends one line (`timestamp  hook  error`) to **`~/.claude/solveit/guard-errors.log`** via `log_guard_error()` in `solve_allow.py`. Check that file if the rules seem to have stopped applying.

### Turn rules (enforced by `stop-affordance-guard.py`)

The Stop hook reads the assistant text since your last message and blocks on:

- **no `▶` handle** — but only when the turn *asserts* something. A turn that asks you a question, a short acknowledgement, a checkpoint report, or one carrying only fenced payload you asked for needs none.
- **prose over ~2200 chars** (`BLOCK_CHARS`) when your last message didn't ask for depth ("explain", "why", "detail", …). Fenced payload is excluded from the count.
- **a trailing menu** — "Want me to… / Should I…?" as the last paragraph. Do the reversible thing, or ask one question about the decision.
- **asking you to paste output or report back** — the agent checks the output itself and says what it saw.
- **`▶ Verify:` on a turn where nothing ran** — that marker means "I ran it"; hand it over as `▶ Try:` instead.
- **an unhedged confident claim on a read-only turn** — "confirmed/proves/clearly" with nothing run and no hedge.
- **a multi-line command** in a `▶` line or shell fence (you copy commands straight from chat).

### Checking how it's going (`solveit-health`)

`solveit-health` (`home/dot_local/bin/executable_solveit-health`, plus the `solveit-health` skill) reads the transcripts and scores every human turn against these rules: `probe%` on asserting turns, `menu%`, median prose chars, edits/turn, tools/turn — with `--days`/`--since`/`--by week`. It also groups guard blocks and separates **bounced runners** (real allowlist candidates, each with the `solve-allow add` line) from hits that are **blocked by design**. Use it after changing a hook: `solveit-health --since <date> --by day`.

### Reads log (`log-reads.py`)

Every `Read`, `Grep`, and `Glob` is appended (timestamp, tool, target) to **`<repo-root>/.solve/reads.log`** so you can see what the agent is looking at and manage context. Read-only shell searches and read-only git allowed by `bash-guard.py` (e.g. `grep`, `find`, `git diff`, `git status`) are logged to the same file as `Bash <command>`. `.solve/` is git-excluded, so the log never dirties the tree or counts toward the cap. It never blocks.

## Task-folder protocol

Anything the agent **executes** lives here (Bash can only run task scripts); app code is still edited directly in the project. Path: `.solve/tasks/<YYYY-MM-DD>-<name>/`:

- `.solve/` is added to the repo's `.git/info/exclude` automatically (by `solve-init.py` on the first prompt), so scratch is invisible to the repo. You can optionally `git init` a task folder to make it its own scratch repo, but it isn't required.
- Numbered, **descriptively named** files `01-run-rspec-for-auth-model.sh`, `02-…` (longer names encouraged). No `.md` is required (dropped 2026-07-23) — instead the script's **first comment line is exactly the command to run it**, at most 1–3 comment lines total. A script can run as soon as it exists.
- The Write tool auto-creates parent dirs, so no `mkdir` is needed (and `mkdir` would be blocked anyway).

## chezmoi sources

| Source (`home/`) | Deployed |
|---|---|
| `dot_claude/settings.json` | `~/.claude/settings.json` (outputStyle + hooks) |
| `dot_claude/CLAUDE.md` | `~/.claude/CLAUDE.md` (SolveIt default section) |
| `dot_claude/output-styles/solveit.md` | `~/.claude/output-styles/solveit.md` |
| `dot_claude/solveit/hooks/executable_edit-guard.py` | `~/.claude/solveit/hooks/edit-guard.py` |
| `dot_claude/solveit/hooks/executable_bash-guard.py` | `~/.claude/solveit/hooks/bash-guard.py` |
| `dot_claude/solveit/hooks/executable_log-reads.py` | `~/.claude/solveit/hooks/log-reads.py` |
| `dot_claude/solveit/hooks/executable_solve-init.py` | `~/.claude/solveit/hooks/solve-init.py` |
| `dot_claude/solveit/hooks/solve_allow.py` | `~/.claude/solveit/hooks/solve_allow.py` (shared allowlist module + CLI) |
| `dot_local/bin/executable_solve-allow` | `~/.local/bin/solve-allow` (PATH wrapper) |
| `dot_agents/skills/solve-baseline/` | `~/.agents/skills/solve-baseline/` (+ claude/codex symlinks) |
| `dot_agents/skills/solve-allow/` | `~/.agents/skills/solve-allow/` (+ claude/codex symlinks) |

Deploy after editing: `chezmoi -S home apply ~/.claude/settings.json ~/.claude/CLAUDE.md ~/.claude/output-styles ~/.claude/solveit ~/.local/bin ~/.agents/skills ~/.claude/skills ~/.codex/skills`.

## Escape hatch: `claude-all`

To run a session with **all** SolveIt constraints off, set `SOLVEIT_OFF=1` in the environment: each of the four hooks (`edit-guard`, `bash-guard`, `log-reads`, `solve-init`) early-returns when it's set, so no line/commit caps, no Bash jail, no reads log, no per-turn reminder. The env var only reaches the hook subprocesses — it does **not** touch `outputStyle`, so the terse solveit *persona* still loads from the system prompt unless you also override it. The `claude-all` alias (`home/dot_zshrc`) does both:

```sh
alias claude-all='SOLVEIT_OFF=1 claude --settings '\''{"outputStyle":"default"}'\'''
```

`--settings` layers a higher-priority override that flips the style back to built-in `default`. Net: guards off, reminder off, persona off.

## Allowlisting specific commands

Commands you explicitly permit bypass the Bash jail. `bash-guard.py` reads `permissions.allow` from your global `~/.claude/settings.json` and the project's `.claude/settings.json` / `.claude/settings.local.json`; any segment matching a `Bash(...)` glob (e.g. `Bash(scripts/anki-sync*)`, mirroring the native permission syntax) is let through. Matching is per-segment, so an allow can't leak into a chained `rm`, and the same entry doubles as Claude's own auto-approve. Separately, read-only searches may redirect to `/dev/null` or use fd-dups (`2>&1`); only redirects to a **real file** are blocked.

### The allowlist primitive (`solve_allow.py`) and the agent knowing it

The allowlist is now a **single source of truth** shared by everything that touches it — the module `~/.claude/solveit/hooks/solve_allow.py`:

- `allow_patterns(cwd)` merges the `Bash(...)` globs from the three settings files. **`bash-guard.py` imports it to decide what passes; `solve-init.py` imports it to *announce* what's allowed.** Because both call the same function, what the agent is *told* it can run can never drift from what the guard actually *allows*.
- `add_pattern` / `remove_pattern` do safe JSON read-modify-write (dedup, `indent=2`) so nothing hand-edits the settings JSON.
- A CLI wraps all three — deployed to PATH as `solve-allow`:
  - `solve-allow list` — print the merged allowlist for the cwd (this one glob, `Bash(solve-allow list)`, is itself globally allowlisted so the agent can run it inside the jail).
  - `solve-allow add "<glob>" [--file F]` / `solve-allow remove "<glob>" [--file F]` — default `--file` is `.claude/settings.local.json`.

**How the agent learns the allowlist.** On the first prompt of a session, `solve-init.py` injects an `ALLOWLISTED for this repo — …` line (the current globs) plus a pointer to `solve-allow list` into context via `additionalContext`. That injection happens **once per session** (marker-gated), so it reflects settings as of the first prompt. The *enforcer* re-reads on every call, so to see a mid-session change run `solve-allow list` — that's always live.

### Curating and extending the allowlist (skills)

Two agent skills sit on top of the primitive:

- **`solve-baseline`** — for the current repo, explores build/test config (`package.json`, `Gemfile`, `tsconfig`, CI) to discover the barebones validation commands (lint, test, typecheck, db setup), proposes a KEEP/DROP plan, and after approval writes the baseline to the committed `.claude/settings.json`. Everything else stays in the task-script jail.
- **`solve-allow`** — adds one in-between allowance from a literal command or a natural-language description ("frontend tests"); resolves it to a narrow glob, confirms, and writes it (local by default). Also the front door for "what am I allowed to run?" via `solve-allow list`.
