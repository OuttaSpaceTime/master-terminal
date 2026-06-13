---
title: claude-solve
tags: [claude-code, solveit, output-styles, hooks, wrapper]
created: 2026-06-13
updated: 2026-06-13
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
2. **Three `PreToolUse` hooks** — the hard layer that does not drift:
   - `Write|Edit|MultiEdit` → `edit-guard.py` (line caps + 4-file task cap)
   - `Bash` → `bash-guard.py` (strict: only runs task scripts)
   - `Read|Grep|Glob` → `log-reads.py` (logs what the agent reads; never blocks)

### Output style behavior (`~/.claude/output-styles/solveit.md`)

- Human sets direction; Claude does **not** propose the next step or a plan unless asked.
- Equally for building, exploring, learning, and planning. A *step* need not be code — it can be "put a breakpoint here", "check this value", "run this command", "drive the app like this and observe", or refining a document you write yourself.
- Socratic by default for understanding/design; **TDD as the primary loop** for app code (task folder is auxiliary only).
- One concrete example first; JRY before DRY; predict-before-running; every reply ends with a verify-it-yourself handoff.
- Claude may run a verification itself but must always hand you a way to verify and tweak it.

### Hard limits (enforced by hooks)

- **≤20 added lines per edit** — a ceiling, not a target (`edit-guard.py`).
- **<20 uncommitted added lines per repo** — once 20+ are uncommitted, edits are blocked; checkpoint due. Counts tracked diff vs HEAD plus untracked file lines, in the file's *enclosing* repo (so a task folder's own repo counts separately).
- **≤4 numbered files per `.claude/tasks/<date>-<name>/`** — a 5th is blocked; commit the folder (its own git repo, ignored by the main repo) and start a new one.
- **Bash only runs task scripts** (`bash-guard.py`, strict). A Bash command is allowed only if every segment is one of: an interpreter (`python`, `sh`, `ruby`, `node`, …) running a file under `.claude/tasks/<X>/` that **exists**, in a folder `<X>` that also contains a `.md` (or a direct `./path` execution of such a file); `git init`; or `cd`. Everything else is blocked — ad-hoc one-liners, read-only shell (`ls`, `grep`, `git status` → use the Read/Grep/Glob tools instead), test runners (`pytest`, `python -m pytest` → wrap in a task script), installs, and chained commands. So everything the agent executes is a reviewable file on disk.
- **No agent commits** — `git commit`/`--amend` by Claude is blocked with its own message; you commit the checkpoints and `--amend` freely.
- **Re-running is unlimited** — running an existing task script (including from an earlier, already-committed task folder) is always allowed and never counts toward the 4-file cap. Repeat work (e.g. tests) = write a descriptive script once, re-run it.

The guard hooks **fail open**: any internal error allows the tool call, so a bug never wedges a session.

### Reads log (`log-reads.py`)

Every `Read`, `Grep`, and `Glob` is appended (timestamp, tool, target) to `<repo-root>/.claude/solveit/reads.log` so you can see what the agent is looking at and manage context. It never blocks. Add `.claude/solveit/` to the repo's `.git/info/exclude`.

## Task-folder protocol

Anything the agent **executes** lives here (Bash can only run task scripts); app code is still edited directly in the project. Path: `.claude/tasks/<YYYY-MM-DD>-<name>/`:

- The folder is its **own** git repo (`git init` inside it); add `.claude/tasks/` and `.claude/solveit/` to the main repo's `.git/info/exclude`.
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

Deploy after editing: `chezmoi -S home apply ~/.claude/output-styles ~/.claude/solveit ~/.local/bin/claude-solve`.

## Why `--settings` (not a flag or global setting)

Claude Code has no `--output-style` flag, and output style is normally a persistent settings field. Passing `outputStyle` through `--settings` is the only way to scope the style *and* the hooks to this one command without changing global config. Confirmed working: a `--settings '{"outputStyle":"…"}'` invocation honors the style.
