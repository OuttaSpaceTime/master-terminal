---
title: SolveIt default mode
tags: [claude-code, solveit, output-styles, hooks]
created: 2026-06-13
updated: 2026-10-28
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

- **One step per turn, no `go`** (since 2026-10-13). It works like a walkthrough: Claude takes the smallest next step, writes its check, hands back, and names the step it would take next; you steer by replying. The caps (30 lines per edit, 1 project file per turn, the uncommitted checkpoints) are what stop a turn doing too much. Before that, every write and run needed a message opening with `go`, and every change was sketched in chat first; both are gone.
- **Every step writes its check to `current.<ext>`, and you run it with `!`** (since 2026-10-15) — Claude archives the previous script, writes a fresh `.solve/tasks/<f>/current.<ext>` that checks *this* step, hands you the fenced one-line `! <run command>` and stops. The script opens with its outline: the run command, then what changed, what it checks, what to look at. Your `!` output lands in the transcript and starts a Claude turn on its own (no prompt, so no `UserPromptSubmit` and no `EDIT_CAP` reset): Claude quotes the lines that matter, names the next step and stops; `edit-guard.py` refuses a project write in a turn your `!` started, so the next edit waits for your next message. From 2026-10-13 to 2026-10-15 Claude ran `current.<ext>` itself (a Stop rule, `CURRENT_MSG`, enforced that); no predict-then-reveal ask either way.
- Equally for building, exploring, learning, and planning. A step that changes nothing — tracing a path, answering *why* — proves its claim the same way: `current.<ext>` prints the real value. Interactive probes (debugger, `bin/rails c`, `dbconsole`) only when you ask for them. **TDD as the primary loop** for app code, in two steps (since 2026-10-22): **red** — Claude writes the test, runs it itself via a numbered task script (`03-red-<name>.sh`; bash-guard only refuses `current.<ext>`), shows the test and the failure, says "`<test>` is red because `<cause>`" and stops so you can double-check it fails for the right reason; **green** — after your next message Claude adds the production code and writes a fresh `current.<ext>` running the same test (a Write, not an `mv` of the red script — `unrun_current` only tracks writes, and the red script stays as the record), and your `!` run shows green. Before 2026-10-22 the red run was a `current.<ext>` too, which cost a `!` round trip plus a nudge per test.
- One concrete example first; JRY before DRY.

### Hard limits (enforced by hooks)

- **≤30 added lines per edit** — a ceiling, not a target (`edit-guard.py`, `CAP`).
- **1 project-code edit per human turn** (`EDIT_CAP`) — the step lands, then Claude hands back. The counter is reset by `solve-init.py` on every prompt; writes under `.solve/` don't count, so probe scripts stay free.
- **Three-tier uncommitted cap** — a checkpoint is due at **30+ *unstaged* lines** (staging what you accept lets work continue), a **warning** at 150 total, and a **hard block at 300 total** where only a real commit helps. Counts tracked diff vs HEAD plus untracked file lines in the enclosing repo. `.solve/` is git-excluded, so task scratch never counts. Since 2026-10-13 a write *inside* a `.solve/tasks/<X>` scratch repo skips the three tiers too: every step archives its `current.<ext>` there, and with the cap the 5th step's write was denied (four archived 8-line scripts = 32 untracked lines), forcing a scratch commit every few steps. Only the 30-per-edit ceiling bounds a scratch write now. Either way Claude never commits: it stops and says what changed; you commit before more is written.
- **Escape valve for a deliberate multi-commit split** — `touch .solve/splitting` (in the session's cwd) lifts the **line caps**: the 30-per-edit ceiling, the 30-line unstaged checkpoint, the 150 warning and the 300 hard block. Two things it never lifts: **`EDIT_CAP`** (still 1 edit per turn, so you keep verifying each step) and the **30-per-edit ceiling under `.solve/tasks/`**, so a runaway probe script is still caught. Use it when you've built one pile on purpose and want to slice it into several commits without the caps fighting you — staging can't help there, because the total is measured vs `HEAD`, so `git add` just moves lines between the staged and dirty buckets. The first project write after you drop the marker stamps that session's id into it; a later chat finds a foreign id, deletes the marker and enforces the caps again — off by default, dies with the chat. Claude is denied writes to the marker, so only you can open the valve.
- **Bash runs task scripts and read-only search/inspection** (`bash-guard.py`). A Bash command is allowed only if every segment is one of: a runner — an interpreter (`python`, `sh`, `ruby`, `node`, …), a `./path` execution, or any non-destructive runner (`bin/rails runner`, `bundle exec ruby`, `npx tsx`, `rake`, …) — invoking a file under `.solve/tasks/<X>/` that **exists**, in a folder `<X>` that also contains a `.md`. **The script path must be the last token** — no args/flags/redirects passed at run time, so a script can't be a generic command forwarder (e.g. `exec bin/rails "$@"`); bake the exact command into the file. (Piping the script's output — `… | grep x` — is fine, since the pipe splits into a separate segment.) **A runner must point at a FILE, never an inline code string** — `bin/rails runner -e "…"`, `ruby -e`, `python -c`, `sh -c "…"` (and `--eval`/`--command`) are blocked; read-only commands' own `-e`/`-c` (e.g. `grep -e`, `head -c`) are unaffected since they match earlier. A segment may instead be a **read-only search/inspection** command (`grep`, `rg`, `find`, `ls`, `cat`, `head`, `tail`, `awk`, … — no `>`/`>>` redirect, and `find` may not `-exec`/`-delete`), optionally wrapped in **read-only shell structure** (`for`/`while`/`if` loops and pipes — each inner command is still validated, so a loop hiding `rm` is still blocked); **`sed` that only prints** (`sed -n 10,40p`, `/a/,/b/p`, `s///` to stdout — no `-i`, `-f`, or `w`/`e`; since 2026-10-28, when `sed -n` line ranges were half of all jail hits); **read-only git** (`diff`, `status`, `log`, `show`, `blame`, `ls-files`, `rev-parse`, `check-ignore`, `merge-base`, `range-diff`, … — the dual-use `worktree`/`branch`/`remote`/`config` only in their read-only forms since 2026-10-28: `worktree list`, `branch --show-current|-vv|--list <pattern>`, `remote -v|get-url|show`, `config --get*|--list`; `tag`/`stash`/`checkout`/`reset` are *not* in the allowlist); `git init` (to create a scratch repo — commits nothing); `cd`; or `mv` **within** `.solve/tasks/` (for renaming a task folder). Segments are split **quote-aware** (a `\|` inside a grep pattern or a `;` inside a commit message no longer mis-splits). Read-only search is allowed because a tool-registration bug ([#52121](https://github.com/anthropics/claude-code/issues/52121)) can drop the `Grep`/`Glob` tools entirely, leaving shell as the only way to look at code; each allowed search **and read-only git** is appended to `reads.log`. Everything else is blocked — ad-hoc one-liners that mutate, **all** repo-mutating git (`add`/`commit`/`--amend`/`checkout`/`reset`/`stash`/`apply`, in any repo), test runners (`pytest`, `python -m pytest` → wrap in a task script), and installs. Commands you explicitly allow via `permissions.allow` `Bash(...)` entries bypass all of this (see below). So everything the agent *executes against the project* is a reviewable file on disk, while *looking* stays cheap.
- **No agent commits — ever** — Claude **never commits anything**. All `git add`/`commit`/`--amend` (and other mutating git) are blocked; you commit every checkpoint (never `--amend` — the `git` wrapper in `.zshrc` blocks it for you too; see [claude-code](claude-code.md#hooks)). The whole philosophy is to keep changes **dirty** so you verify and commit. Only `git init` (to make a task folder its own scratch repo) and read-only git are allowed. This covers `.solve/tasks/` scratch repos too (restored 2026-09-23 after a week where Claude could stage/commit there, which let it clear its own scratch caps); commit one from nvim with `<leader>gg` on a file inside it.
- **Subagents run outside the guards** (since 2026-10-28). When you hand a mechanical task to a subagent ("let's do this with a subagent"), its tool calls carry `agent_id` (Claude Code docs, Hooks → Common input fields), and `bash-guard.py` and `edit-guard.py` let them through: no Bash jail, no line or turn caps. Only the `.solve/splitting` check still applies, so a subagent can't lift the main agent's caps. `solve-init.py` tells the main agent to spawn one only when you ask, and to brief it to commit in small single-line steps (no trailer, no amend, no push). Your project hooks (migrations, `schema.rb`, reek) still run for subagents.
- **No go gate** (removed 2026-10-13). `solve-init.py` no longer writes a `<session>.go` flag, and neither `edit-guard.py` nor `bash-guard.py` checks one: a script is written and run in the same turn, and you read it in your buffer afterwards (`current.<ext>` excepted since 2026-10-15: you run that one). (2026-09-16 to 2026-10-13 the gate was the chat sketch plus your `go`; before that, the mtime check `written_since` cost a round trip per probe.)
- **One live script: `current.<ext>`** — the script being worked on always sits at `.solve/tasks/<folder>/current.<ext>`, one stable path you can keep open in a buffer (a rewrite just reloads it). The extension follows the language (`current.rb`, `current.py`, `current.sh`, `current.js`). Each step either extends it by one question (since 2026-10-21) or archives it under the descriptive numbered name it earned — `mv .solve/tasks/<f>/current.rb .solve/tasks/<f>/02-probe-token-expiry.rb` (the `mv`-within-`.solve/tasks/` allowance) — and writes a fresh `current.<ext>`. `edit-guard.py` blocks a *new* `current.<ext>` (path absent: archived away, or another extension) while the one written before your last prompt is unrun; project edits and in-place fixes of it still land (before 2026-10-21 it held project edits instead).
- **Re-running is unlimited** — running an **unchanged** archived task script is always allowed. Repeat work (e.g. tests) = re-run the archived file.
- **Only you run `current.<ext>`** — `bash-guard.py` refuses any Claude Bash segment whose last token is a `.solve/tasks/<X>/current.<ext>` (`cat`/`mv` of it still pass; an allowlist entry like `bin/rails test:*` can't override it), and `edit-guard.py` (`unrun_current`) blocks a project write while the `current.<ext>` Claude wrote before your last prompt has no `<bash-input>` run of it after it in the transcript. A `current.<ext>` written in the same turn, a write a guard denied, and rewriting `current.<ext>` itself never hold anything. `!` commands don't go through `PreToolUse`, so the jail never blocks you.

The guard hooks **fail open**: any internal error allows the tool call, so a bug never wedges a session. Since 2026-07-30 a failure is no longer silent — each hook appends one line (`timestamp  hook  error`) to **`~/.claude/solveit/guard-errors.log`** via `log_guard_error()` in `solve_allow.py`. Check that file if the rules seem to have stopped applying.

### Turn rules (enforced by `stop-affordance-guard.py`)

The Stop hook reads the turn since your last message — its text and its tool calls — and blocks on:

- **prose over ~2200 chars** (`BLOCK_CHARS`) when your last message didn't ask for depth ("explain", "why", "detail", …). Fenced payload is excluded from the count.
- **a trailing menu** — "Want me to… / Should I…?" as the last paragraph. Do the reversible thing, or ask one question about the decision.
- **asking you to paste output or report back** — your `!` output is already in the transcript; the agent reads it there.
- **an unhedged confident claim on a read-only turn** — "confirmed/proves/clearly" with nothing run and no hedge. A turn started by your `!` output (last user entry is `<bash-stdout>`) counts as having run.
- **a multi-line command** in a shell fence or a `▶` line (you copy commands straight from chat). A shell fence whose **first line is a comment** is read as a script listing, not a command to paste — that is the task-script convention (first comment line = the run command), so showing a multi-line bash script is fine.
- **a task script written that the turn neither ran nor showed** (`SCRIPT_MSG`) — the turn wrote a file under `.solve/tasks/`, ran nothing, and its text neither names the script nor contains a fenced block. For `current.<ext>`, the fenced `! <run command>` satisfies it.

The turn's closing message lands in the transcript a moment after the Stop hook fires, so the hook polls (`STOP_GUARD_POLL` × `STOP_GUARD_POLL_INTERVAL`, ~2 s max) until the last user/assistant entry is assistant text, then checks. It used to wait for a `▶` to appear instead.

### Checking how it's going (`solveit-health`)

`solveit-health` (`home/dot_local/bin/executable_solveit-health`, plus the `solveit-health` skill) reads the transcripts and scores every human turn against these rules: `verified%` (turns that landed a write where Claude ran `current.<ext>` after it — the 2026-10-13 rule; it drops toward 0% from 2026-10-15, when you run `current.<ext>` instead), `menu%`, median prose chars, edits/turn, tools/turn — with `--days`/`--since`/`--by week`. It also groups guard blocks and separates **bounced runners** (real allowlist candidates, each with the `solve-allow add` line) from hits that are **blocked by design**. Use it after changing a hook: `solveit-health --since <date> --by day`.

### Reads log (`log-reads.py`)

Every `Read`, `Grep`, and `Glob` is appended (timestamp, tool, target) to **`<repo-root>/.solve/reads.log`** so you can see what the agent is looking at and manage context. Read-only shell searches and read-only git allowed by `bash-guard.py` (e.g. `grep`, `find`, `git diff`, `git status`) are logged to the same file as `Bash <command>`. `.solve/` is git-excluded, so the log never dirties the tree or counts toward the cap. It never blocks.

## Task-folder protocol

Anything the agent **executes** lives here (Bash can only run task scripts); app code is still edited directly in the project. Path: `.solve/tasks/<YYYY-MM-DD>-<name>/`:

- `.solve/` is added to the repo's `.git/info/exclude` automatically (by `solve-init.py` on the first prompt), so scratch is invisible to the repo. You can optionally `git init` a task folder to make it its own scratch repo, but it isn't required.
- Numbered, **descriptively named** files `01-run-rspec-for-auth-model.sh`, `02-…` (longer names encouraged). No `.md` is required (dropped 2026-07-23) — instead the script's **first comment line is exactly the command to run it**, followed by at most 3 outline lines (what changed, what it checks, what to look at), then the debug hint `~/.claude/CLAUDE.md` gives per runner (Ruby `debugger`, Node `debugger;` under `node inspect`, shell `set -x`; run it from a terminal pane, since without a TTY the debugger quits at the breakpoint with exit 0 or hangs waiting for input, and skips the rest). A script is written and run in the same turn.
- The Write tool auto-creates parent dirs, so no `mkdir` is needed (and `mkdir` would be blocked anyway).

## chezmoi sources

| Source (`home/`) | Deployed |
|---|---|
| `dot_claude/modify_settings.json` | `~/.claude/settings.json` (merge script: hooks enforced, UI keys passed through) |
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
