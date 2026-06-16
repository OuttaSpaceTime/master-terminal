---
title: claude-solve
tags: [claude-code, solveit, output-styles, hooks, wrapper]
created: 2026-06-13
updated: 2026-06-15
---

# claude-solve

A wrapper that runs Claude Code in **SolveIt mode** — incremental, human-as-agent work with hard guardrails against agent eagerness. See [Solveit Method](solveit-method.md) for the underlying philosophy.

## What it is

`claude-solve` is a thin wrapper. The whole command is:

```bash
claude --settings ~/.claude/solveit/settings.json --name solveit "$@"
```

It activates everything through one flag, `--settings`, which loads an **additional** settings layer for that invocation only. It is additive (your normal user settings, plugins, statusline, and existing hooks still apply), ephemeral (nothing global changes; plain `claude` is unaffected), and hooks accumulate across sources rather than replacing each other.

`--name solveit` is cosmetic — it labels the session so you can see you are in the constrained mode.

## What it activates

`~/.claude/solveit/settings.json` turns on exactly two mechanisms:

1. **`outputStyle: "solveit"`** — the soft layer. Injects the SolveIt method into the system prompt and re-asserts it as a reminder every turn (this is what fights eager-drift over long sessions — `--append-system-prompt` injects only once and fades). Built with `keep-coding-instructions: true` so Claude keeps its engineering ability.
2. **A `UserPromptSubmit` hook** (`solve-init.py`) — on your **first message** of a session (guarded once-per-session by a marker in `~/.claude/solveit/state/<session_id>.solve`, so idle launches leave no clutter), creates a per-session task folder `.claude/tasks/<date-time>-solve/` with a Pólya-structured `solve.md`, `git init`s that folder **and commits the scaffold** (so the folder's own repo starts at a clean baseline and the first write doesn't immediately trip the uncommitted-line cap), appends `.claude/tasks/` + `.claude/solveit/` to the main repo's `.git/info/exclude`, and injects context telling Claude to greet, treat the message as the problem, **rename the folder in place** (`mv …-solve <date>-<slug>`) once the problem is clear, and in that first answer hand the human the commands to open it themselves (`cd .claude/tasks/<date>-<slug>` and `nvim .../solve.md`). `solve.md` is the **human's** document and the session's source of truth (Understand → Devise a plan → Carry out → Look back) — Claude does **not** write findings/plans into it on its own; it edits `solve.md` only when explicitly asked, and reports findings in chat otherwise. Note: interactive Claude can't speak first, so the greeting lands on that first turn, not at launch.
3. **Three `PreToolUse` hooks** — the hard layer that does not drift:
   - `Write|Edit|MultiEdit` → `edit-guard.py` (line caps + 4-file task cap)
   - `Bash` → `bash-guard.py` (strict: only runs task scripts)
   - `Read|Grep|Glob` → `log-reads.py` (logs what the agent reads; never blocks). Read-only shell searches and read-only git allowed by `bash-guard.py` are logged to the same `reads.log` (in the session's scratch folder).

### Output style behavior (`~/.claude/output-styles/solveit.md`)

- Human sets direction; Claude does **not** propose the next step or a plan unless asked.
- Equally for building, exploring, learning, and planning. A *step* need not be code — it can be "put a breakpoint here", "check this value", "run this command", "drive the app like this and observe", or refining a document you write yourself.
- Socratic by default for understanding/design; **TDD as the primary loop** for app code (task folder is auxiliary only).
- One concrete example first; JRY before DRY; predict-before-running; every reply ends with a verify-it-yourself handoff.
- Claude may run a verification itself but must always hand you a way to verify and tweak it.

### Hard limits (enforced by hooks)

- **≤20 added lines per edit** — a ceiling, not a target (`edit-guard.py`).
- **<20 uncommitted added lines per repo** — once 20+ are uncommitted, edits are blocked; checkpoint due. Counts tracked diff vs HEAD plus untracked file lines, in the file's *enclosing* repo (so a task folder's own repo counts separately). The **same 20-line cap applies to the main repo and to a `.claude/tasks/` scratch repo** — either way Claude never commits: it stops and tells the human what changed, and the human commits before more is written.
- **≤4 numbered files per `.claude/tasks/<date>-<name>/`** — a 5th is blocked; start a new dated folder (Claude never commits — scratch just rolls into a fresh folder).
- **Bash runs task scripts and read-only search/inspection** (`bash-guard.py`). A Bash command is allowed only if every segment is one of: a runner — an interpreter (`python`, `sh`, `ruby`, `node`, …), a `./path` execution, or any non-destructive runner (`bin/rails runner`, `bundle exec ruby`, `npx tsx`, `rake`, …) — invoking a file under `.claude/tasks/<X>/` that **exists**, in a folder `<X>` that also contains a `.md`. **The script path must be the last token** — no args/flags/redirects passed at run time, so a script can't be a generic command forwarder (e.g. `exec bin/rails "$@"`); bake the exact command into the file. (Piping the script's output — `… | grep x` — is fine, since the pipe splits into a separate segment.) **A runner must point at a FILE, never an inline code string** — `bin/rails runner -e "…"`, `ruby -e`, `python -c`, `sh -c "…"` (and `--eval`/`--command`) are blocked; read-only commands' own `-e`/`-c` (e.g. `grep -e`, `head -c`) are unaffected since they match earlier. A segment may instead be a **read-only search/inspection** command (`grep`, `rg`, `find`, `ls`, `cat`, `head`, `tail`, `awk`, … — no `>`/`>>` redirect, and `find` may not `-exec`/`-delete`), optionally wrapped in **read-only shell structure** (`for`/`while`/`if` loops and pipes — each inner command is still validated, so a loop hiding `rm` is still blocked); **read-only git** (`diff`, `status`, `log`, `show`, `blame`, `ls-files`, `rev-parse`, … — the dual-use `branch`/`tag`/`remote`/`stash`/`checkout`/`reset` are *not* in the allowlist); `git init` (to create a scratch repo — commits nothing); `cd`; or `mv` **within** `.claude/tasks/` (for renaming the solve folder). Segments are split **quote-aware** (a `\|` inside a grep pattern or a `;` inside a commit message no longer mis-splits). Read-only search is allowed because a tool-registration bug ([#52121](https://github.com/anthropics/claude-code/issues/52121)) can drop the `Grep`/`Glob` tools entirely, leaving shell as the only way to look at code; each allowed search **and read-only git** is appended to `reads.log`. Everything else is blocked — ad-hoc one-liners that mutate, **all** repo-mutating git (`add`/`commit`/`--amend`/`checkout`/`reset`/`stash`/`apply`, in any repo), test runners (`pytest`, `python -m pytest` → wrap in a task script), and installs. So everything the agent *executes against the project* is a reviewable file on disk, while *looking* stays cheap.
- **No agent commits — ever** — Claude **never commits anything**, not the main repo and not its own `.claude/tasks/` scratch repos. All `git add`/`commit`/`--amend` (and other mutating git) are blocked; you commit every checkpoint (main *and* scratch) and `--amend` freely. The whole philosophy is to keep changes **dirty** so you verify and commit. Only `git init` (create a scratch repo) and read-only git are allowed.
- **Re-running is unlimited** — running an existing task script (including from an earlier task folder) is always allowed and never counts toward the 4-file cap. Repeat work (e.g. tests) = write a descriptive script once, re-run it.

The guard hooks **fail open**: any internal error allows the tool call, so a bug never wedges a session.

### Reads log (`log-reads.py`)

Every `Read`, `Grep`, and `Glob` is appended (timestamp, tool, target) to **`reads.log` inside the session's scratch/solve folder** (e.g. `.claude/tasks/<date>-<slug>/reads.log`) so you can see what the agent is looking at and manage context. Read-only shell searches and read-only git allowed by `bash-guard.py` (e.g. `grep`, `find`, `git diff`, `git status`) are logged to the same file as `Bash <command>`. The location is tracked via the session marker (`~/.claude/solveit/state/<session_id>.solve`, which stores the folder path); `bash-guard.py` repoints it when the agent `mv`-renames the folder, so the log follows the rename. `reads.log` is added to the scratch repo's `.git/info/exclude` so it never counts toward the 20-line cap. It never blocks. If no scratch folder is resolvable, it falls back to `<repo-root>/.claude/solveit/reads.log`.

## Task-folder protocol

Anything the agent **executes** lives here (Bash can only run task scripts); app code is still edited directly in the project. Path: `.claude/tasks/<YYYY-MM-DD>-<name>/`:

- The folder is its **own** git repo (`git init` inside it — this makes the 20-line cap count it; Claude never commits it, you do); add `.claude/tasks/` and `.claude/solveit/` to the main repo's `.git/info/exclude`.
- Numbered, **descriptively named** files `01-run-rspec-for-auth-model.sh` … through `04-…` (longer names encouraged), plus one `.md` describing each file (what it does, how to run, how to verify). A script runs only once both the `.md` and the script exist.
- The Write tool auto-creates parent dirs, so no `mkdir` is needed (and `mkdir` would be blocked anyway).

## chezmoi sources

| Source (`home/`) | Deployed |
|---|---|
| `dot_local/bin/executable_claude-solve` | `~/.local/bin/claude-solve` |
| `dot_claude/output-styles/solveit.md` | `~/.claude/output-styles/solveit.md` |
| `dot_claude/solveit/settings.json` | `~/.claude/solveit/settings.json` |
| `dot_claude/solveit/hooks/executable_edit-guard.py` | `~/.claude/solveit/hooks/edit-guard.py` |
| `dot_claude/solveit/hooks/executable_bash-guard.py` | `~/.claude/solveit/hooks/bash-guard.py` |
| `dot_claude/solveit/hooks/executable_log-reads.py` | `~/.claude/solveit/hooks/log-reads.py` |
| `dot_claude/solveit/hooks/executable_solve-init.py` | `~/.claude/solveit/hooks/solve-init.py` |

Deploy after editing: `chezmoi -S home apply ~/.claude/output-styles ~/.claude/solveit ~/.local/bin/claude-solve`.

## Why `--settings` (not a flag or global setting)

Claude Code has no `--output-style` flag, and output style is normally a persistent settings field. Passing `outputStyle` through `--settings` is the only way to scope the style *and* the hooks to this one command without changing global config. Confirmed working: a `--settings '{"outputStyle":"…"}'` invocation honors the style.
