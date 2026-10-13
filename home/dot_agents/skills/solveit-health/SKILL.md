---
name: solveit-health
description: Check how SolveIt mode is actually going by reading Claude Code transcripts — score every human turn against the rules the hooks enforce (current.<ext> run after each write, menus, prose length, edits per turn), count what keeps getting blocked, and propose the allowlist entries that would stop the repeated jail hits. Use when the user asks "how is solveit doing", "are the hooks working", "what keeps getting blocked", "what should we allow", "check solveit health", "did the new rules help", or after changing a SolveIt hook and wanting to know whether the numbers moved.
---

# SolveIt health

Reports how the mode is behaving from evidence, not impression. The engine is
`solveit-health` (on PATH via `~/.local/bin`); this skill is how to read it and
what to do about it.

## Run it

```
solveit-health                      # last 7 days, one bucket
solveit-health --days 30 --by week  # trend
solveit-health --blocks             # just blocks + allowlist candidates
solveit-health --since 2026-07-30   # since a hook change
```

Add `--by day` when you are checking whether a change that landed today worked.

## Read it

| column | what it is | target |
|---|---|---|
| `verified%` | share of turns that landed a write where `current.<ext>` ran after the last one. Turns that wrote nothing are excluded | ≥95% |
| `menu%` | turns ending by offering the human a choice of the agent's plans ("Want me to…?") | 0% |
| `p50 chars` | median prose per turn, fenced payload excluded | <1200 |
| `edits/t` | project-code edits per turn (`.solve/` scratch excluded) | 1–2 |
| `tools/t` | tool calls of any kind per turn | <10 |

`tools/t` above ~10 is the run-ahead tell: those turns average 3× the prose and
end in a menu twice as often. If `verified%` drops, steps are landing without their
check — read the `unverified step` block count next to it.

## Act on it

- **`bounced runners`** — real commands the jail rejected. Each line comes with the
  `solve-allow add '<head>:*'` that would stop it recurring. Propose the ones that
  are genuine validation commands (test runners, linters, migrations, dev scripts);
  skip anything that mutates the repo.
- **`blocked by design` count** — jail hits on `echo`/`sed`/`mkdir`/git-writes.
  These do *not* want an allowance; a rising count means the agent keeps reaching
  for shell instead of writing a task script.
- **`guard blocks`** — one label per hook. A label that dominates points at a rule
  that is either mis-tuned or teaching nothing. `checkpoint due` and `total cap`
  climbing means the human is not committing often enough, not that the cap is wrong.
- **Cap tuning** — the caps live in
  `home/dot_claude/solveit/hooks/executable_edit-guard.py` (`CAP`, `EDIT_CAP`,
  `DIRTY_CAP`, `WARN_CAP`, `TOTAL_CAP`) and
  `executable_stop-affordance-guard.py` (`BLOCK_CHARS`). Change one at a time and
  re-run with `--since <that date>`.

Report the table, the two or three lines that actually moved, and the allowlist
entries worth adding. Nothing else — this skill exists to replace impressions with
five numbers.
