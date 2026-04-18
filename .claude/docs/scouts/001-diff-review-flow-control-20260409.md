# Scout: diff-review flow-control bugs — 2026-04-09

## Problem

diff-review's interactive walkthrough has three flow-control failures:

1. **Auto-advance on discussion** — User pauses mid-CP2 to discuss a change, model jumps to CP3
2. **No resume** — After discussion, model restarts from top instead of resuming where it left off
3. **Batch-marking without showing** — Model marks files ✅ reviewed without having shown the diff

## Root Cause

The skill has no explicit "where am I?" protocol. Three gaps:

- **No discussion-return rule:** "Discussion is first-class" (line 39) has no enforcement — no instruction on what to do *after* discussion ends
- **No resume protocol:** Progress Tracker exists but the model is never told to read it when resuming
- **No status-marking constraint:** "Mark ✅ after" (line 157) doesn't require the diff was shown or the developer confirmed

## Decisions

| Gate | Decision | Status |
|------|----------|--------|
| Where to add rules | `SKILL.md` only (not interactive-principles) | [DECIDED] |
| Status-marking strength | Hard prohibition + developer must confirm | [DECIDED] |

## Scope

- **Now:** Three additions to `SKILL.md` — discussion-return rule, resume protocol, status-marking with developer confirmation. Condensation pass to offset added length.
- **Later:** Extract discussion-return to `interactive-principles.md` if other skills show same bug
- **Out:** No changes to interactive-principles, notes file format, or checkpoint structure

If implementation discovers work outside these boundaries, it must STOP and ask — not silently expand scope.

## Risks

1. **Instruction bloat** — Skill already 280 lines. Mitigate with condensation pass.
2. **Confirmation friction** — On large diffs, per-file confirmation could feel tedious. Mitigate: any forward-moving response counts as acceptance.

## Readiness

Ready to plan. No blockers.
