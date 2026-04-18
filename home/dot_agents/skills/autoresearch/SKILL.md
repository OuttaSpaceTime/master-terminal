---
name: autoresearch
description: >
  Run an autonomous improve-measure-learn loop for numeric optimization or qualitative
  exploration. Use when the user wants repeated experiments, iterative optimization, or a
  best-of-many search instead of a one-shot answer. Distinct from `/research` for a single
  briefing and `/plan` for a fixed implementation strategy.
---

# Autoresearch

Autonomous research loop: change → evaluate → keep/revert → learn → repeat.

Read `references/session-schema.md` for `.autoresearch.md` and `.autoresearch.jsonl` formats.

## Interactive Constraints (mandatory)
- ONE concept per message, under 200 words of prose. Pause after each step or checkpoint.
- 3-12 lines of prose per message. If more is needed, split.
- Code snippets: use fenced blocks with `lang path:start-end` info string and enclosing context.
- If developer says "skip" or "I know this," fast-forward immediately.
- For additional shared principles (scope awareness, handling disagreement), see `references/interactive-principles.md`.

## Detecting Mode

- **Metric mode**: numeric measurement. Clues: "minimize", "maximize", "reduce",
  "speed up", numbers, units, benchmarks.
- **Exploration mode**: no single number. Clues: "improve", "find the best",
  "try different approaches", skills, rules, prompts, architecture.

If uncertain, ask one clarifying question: "Should I treat success as hitting a
numeric target (metric mode) or as qualitatively better output against a rubric
(exploration mode)?"

Parse `--max N` for iteration cap.

Parse **goal values** ("under 60s", "hit 90+", "below 100 errors") → record as
`target` with direction. Stop early when met.

## Session Setup

If `.autoresearch.md` exists → resume (read config + history, print status, enter loop).
If resuming with `--max N`, the new value overrides the original max.
**On resume, always re-run the baseline measurement** before entering the loop.
The codebase may have changed between sessions — a stale baseline produces
misleading comparisons.

### New Session

#### 1. Collect the Objective
Get the user's goal. Vague is fine — you'll research what "better" means.

#### 2. Research the Target
Read files in scope. Understand what exists, what to measure, what could break.

#### 3. Propose the Workflow
Present **2-3 options with tradeoffs** for each aspect:

**Measurement** (metric mode): Propose 2-3 metric commands tailored to the
project's stack. Check CLAUDE.md/.claude/rules/ for constraints. For multi-step
measurements (start server → run tool → extract number), write a wrapper script.
**Verify the metric command is side-effect-free** — some scripts (e.g., budget
checkers, migration tools) exit non-zero or mutate state as a side effect of
measuring. If the obvious metric command has side effects, write a wrapper that
extracts just the number (e.g., run `tsc --noEmit` and count errors rather than
using a budget script that enforces limits). Test the metric command in baseline
before entering the loop.
Estimate per-iteration cost; mention it when proposing iteration count.

**Scenarios** (exploration mode): Propose breadth (many cases), depth (hardest
cases), or progressive (start small, expand later).

**Validation**: Full (all checks), light (lint+compile), targeted (changed files
only), or none. For non-code targets (skills, prompts, docs): "validation"
means a sanity check (syntax valid, runs without error, key functions exist).
If no validation is sensible, set to "none" and skip.

**Scope** — distinguish two scopes:
- **Modify scope**: files you'll change. Keep tight.
- **Read scope**: files you'll read for context/profiling. Can be broad.

#### 4. User Decides
Wait for choice. If they defer, pick your recommendation with a one-line rationale.

#### 5. Create Session Files
Write `.autoresearch.md` and `.autoresearch.jsonl` per the schema.

#### 6. Run Baseline
Experiment #0 verifies the workflow and establishes the starting point.

**Git**: If in a repo (`git: existing`), use git normally. If not (`git: own`),
run `git init && git add -A && git commit -m "autoresearch: initial state"`.
Offer cleanup (`rm -rf .git`) when the session ends.

## The Autonomous Loop

Run autonomously until iteration cap, target met, or user interrupts (Ctrl+C).

### Metric Mode

**First iteration**: profile/analyze before guessing — run verbose output, check
bottlenecks, read code. Form a data-informed hypothesis, not a blind guess.

```
For each iteration:
  1. THINK     — Review history. Form hypothesis: "I believe [change] will
                 [improve metric] because [reasoning]."
                 After 3+ experiments, try combining 2-3 promising reverted
                 ideas that may compound.
  2. IMPLEMENT — Targeted changes within modify scope. One idea per experiment.
  3. VALIDATE  — Run validation. Fail → revert, log "invalid", continue.
  4. MEASURE   — Run metric command. If a single run has >5-10% natural
                 variance (e.g., test duration, Lighthouse score), run 3x
                 and use the median. Skip re-runs for deterministic metrics
                 (error count, bundle size).
  5. EVALUATE  — Compare to best. Require >2% improvement for noisy metrics.
                 Target met → stop. Improved → commit, log "improvement".
                 Not improved → revert, log "regression".
  6. LOG       — Append to .autoresearch.jsonl.
  7. STATUS    — Print: [#N/max] ✓/✗ value (±% vs best) — description
```

### Exploration Mode

**First iteration**: read and analyze what exists before changing. Identify
strengths, weaknesses, and the highest-leverage gap vs the objective.

**Before the loop**, define a **rubric** — 3-5 concrete criteria derived from
the objective. Rules for good criteria:
- Each criterion scores **pass / partial / fail** (not 1-10 scales).
- Always include a "no regressions" criterion: diff old vs new and verify
  every original point is preserved or consciously superseded — not just that
  the overall structure looks similar. Losing a specific convention or detail
  counts as a regression even if the surrounding text improved.
- If two reviewers would disagree on the score, the criterion is too vague —
  make it more specific.

Examples:
- Skills/prompts: follows intent? handles edge cases? actionable without clarification?
- Architecture: correct data flow? minimal file changes? testable in isolation?

Record the rubric in `.autoresearch.md`.

```
For each iteration:
  1. THINK     — Review learnings. Form hypothesis from prior experiments.
                 After 3+, look for meta-patterns: which criteria resist
                 improvement? Can winning elements from different experiments
                 be combined?
  2. SNAPSHOT  — Save current version of files in scope.
  3. IMPLEMENT — One coherent idea per experiment.
  4. VALIDATE  — If configured. Fail → revert, log "invalid", continue.
  5. EVALUATE  — Compare old vs new against the rubric.
                 **With subagents available**: Blind A/B comparison —
                   a. Save output from OLD version as "output_A.txt" (no label)
                   b. Save output from NEW version as "output_B.txt" (no label)
                   c. Spawn a grader subagent that scores both A and B against
                      the rubric WITHOUT knowing which is old vs new
                   d. Only then reveal labels; record the winner
                 **Without subagents (single-agent mode)**: Sequential rubric
                 scoring — score the OLD version first, then the NEW version,
                 using the same rubric. Acknowledge this is not blind; compensate
                 by being strict about rubric criteria (pass/partial/fail only)
                 and writing scores before comparing them.
                 **Counter recency bias**: before scoring NEW, re-read OLD and
                 note what it does well. If the baseline already scores pass on
                 all rubric criteria, the bar for "improvement" is higher —
                 require clear wins on at least one criterion, not marginal ones.
  6. DECIDE    — Majority wins → commit + log "improvement".
                 Tie with no regressions on any criterion → commit + log
                 "improvement" (or revert if the change adds complexity for
                 no clear gain — use judgment, but log must match the action).
                 Any criterion regressed → revert + log "regression".
                 The JSONL `type` field must match the actual keep/revert
                 decision. Never mark "regression" for a kept change or
                 vice versa.
  7. LOG + STATUS — Print: [#N/max] ✓/✗ Won X/Y scenarios — description
```

**Evaluation by target type:**
- **Skills/prompts**: spawn subagents with the skill loaded, label outputs A/B.
  Prefer real execution over mental simulation.
- **Architecture**: trace how each design handles the scenario. For wholesale
  alternatives, use git branches (`exp-N`). Sketch before implementing — reject
  at sketch level if it clearly loses on the rubric.

## Guardrails

- **Scope discipline**: never modify files outside modify scope.
- **Validate before measuring**: broken code = "invalid", not "regression".
- **Stay autonomous**: don't ask permission during the loop.
- **Error resilience**: env/tool errors → log "error", continue.
- **Circuit breaker**: 3 consecutive "error"-type entries (environment/tool
  failures, not regressions) → stop and ask for guidance. This indicates the
  workflow itself may be misconfigured.
- **Stall detection**: 3 consecutive regressions (not errors) → pause and
  reassess. This likely means remaining improvements are harder than the
  current approach can reach. Print a summary of what's been tried, suggest
  a different strategy angle, and ask whether to continue or stop.
- **One idea per experiment**. Exception: batch reduction tasks (errors, warnings)
  → work in themed batches ("fix all `noImplicitAny` in auth module"). A batch
  counts as one experiment: one commit, one measurement, one revert-or-keep
  decision. Do not measure individual items within a batch.
- **Learn from history**: never repeat a failed approach without a specific reason.

## Updating Session Files

After every experiment: append to `.autoresearch.jsonl` (never modify previous
lines), update `.autoresearch.md` (Current Best, Key Learnings, Summary).
Capture *why* things work in Key Learnings, not just that they do.

## When the Loop Ends

1. **Summary**: mode, experiments run, improvements found, best value (±% vs
   baseline). If target was set, note whether met.
2. **Top 3 learnings** from the session.
3. **Actionable next steps**: what the user should do now (run full test suite,
   monitor in production, scope a follow-up session for remaining work).
4. **Unexplored directions** for future sessions.
5. If `git: own`, offer to clean up `.git`.
