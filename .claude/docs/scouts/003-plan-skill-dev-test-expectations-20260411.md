# Scout 003 — Plan skill: developer test-expectations sub-step

## Request

> update the plan skill to have a specific section about tests — what the dev expects to be tested, with some potential steps

## Final Intent (after clarification)

Add a **conversational sub-step** to `/plan`'s interactive flow where the planner asks the developer what they expect to be tested. The developer's answers, plus planner-surfaced gaps, feed the **existing** Testing Strategy table. **No new section in the produced artifact.** The output template does not change.

**Core framing (the why):** thinking through what needs to be tested is itself the forcing function that makes the developer reason through full change scope. Testing expectations *are* loop-closure reasoning — if you can't say what proves it's done, you haven't closed the loop. This is why the sub-step belongs inside Checkpoint 2 (Loop Closure): it's the natural finish of that checkpoint, not an addition tacked onto it.

## Scope

Doc-only change to one file in the chezmoi source tree:

- `home/dot_agents/skills/plan/SKILL.md`

No change to:
- `home/dot_agents/skills/plan/references/workflow.md` (output template unchanged)
- `/scout`, `/sketch`, `/review`, or any runtime code

Deploys via `chezmoi -S home apply`. Validation = `chezmoi -S home diff` + re-read.

## Current State (verified)

- `SKILL.md:103-109` — Guided Checkpoints, three entries. Checkpoint 2 is "Loop Closure — Walk the execution flow trigger-to-completion. Make the developer trace along. Make explicit: what starts the work, what state changes, what downstream outcome proves the loop closed."
- `SKILL.md:184-192` — Step 10 "Define Testing Strategy" (planner output, stays as-is structurally).
- `SKILL.md:22` — "Scout exists? Inherit it, validate against code, compress into implementation steps. Never redo scout work." (Relevant because scout does NOT currently elicit dev test expectations — its Test Scenario Landscape is planner-inferred. So the new sub-step runs in both Mode A and Mode B regardless of scout presence.)

## Design

### Behavior of the new sub-step (inside Checkpoint 2)

After the developer traces the new execution flow, the planner asks — in the dev's framing — *"what would you expect to be tested to prove this loop closes?"* The developer answers in free form, at whatever granularity feels natural. The planner:

1. Captures the expectations conversationally (not in an artifact section).
2. Folds each expectation into the Testing Strategy table as concrete rows when the table is produced in Step 10.
3. Conversationally flags any coverage the dev didn't mention that the loop needs — *"adding X because without it the trigger→outcome path isn't verified"* — and adds corresponding rows.
4. Never silently "corrects" the developer's framing. Dev points go in as the dev stated them; planner additions are clearly separated in conversation.

### Decision gates (resolved)

1. **Interpretation** — `[DECIDED]` interactive extension only, no artifact change.
2. **Placement** — `[DECIDED]` sub-step inside Checkpoint 2, framed as the natural completion of loop-closure reasoning.
3. **Relationship to Testing Strategy table** — `[DECIDED]` feeds it directly; no new column, no enforcement; the merge is conversational and natural.
4. **Shape of "potential steps"** — `[DECIDED]` free-form dev bullets in conversation; formal precondition→action→expected shape only appears when the Testing Strategy table materializes.
5. **Mode A inheritance** — `[DECIDED]` no special-case; scout doesn't collect dev expectations, so the sub-step runs regardless of mode.

**Anti-patterns to call out in the SKILL.md edit:**
- Do NOT introduce a new output section for this.
- Do NOT silently overwrite or "correct" the developer's expectations when merging into the Testing Strategy table.
- Do NOT skip the sub-step when a scout exists — scout doesn't produce this input.

## File Impact

| File | Change |
| --- | --- |
| `home/dot_agents/skills/plan/SKILL.md` | Extend Checkpoint 2 description with a test-expectations sub-step + the "why" framing (testing = loop-closure reasoning). Add one line to Step 10 noting that expectations surfaced in Checkpoint 2 must be merged into the Testing Strategy table, with planner-added gap rows clearly distinguishable in the conversation. |

## Risks

- **Drift back into duplication.** Future runs might create a de-facto new section in the artifact. *Mitigation:* the SKILL.md edit must say explicitly "this is a conversational sub-step — it does not add a section to the artifact; it feeds the Testing Strategy table."
- **Skipped when scout exists.** A future reader might assume scout already covered it. *Mitigation:* one-line note that scout's Test Scenario Landscape is planner-inferred and does not substitute for dev-elicited expectations.
- **Checkpoint 2 bloat.** Already the heaviest checkpoint. *Mitigation:* frame the sub-step as the *finish* of loop-closure, not an addition — it replaces ad-hoc "what proves it's done" talk with a structured prompt.

## Now / Later / Out

- **Now**: single edit to `SKILL.md` — extend Checkpoint 2 description, add one-line amendment to Step 10.
- **Later**: consider porting same sub-step to `/sketch` if the pattern proves useful.
- **Out**: any change to `references/workflow.md`, any new artifact section, any change to `/scout` or other skills.

> If implementation discovers work outside these boundaries, it must STOP and ask — not silently expand scope.

## Handoff

Ready for `/sketch` — this is a single-file, well-scoped doc edit with all decisions resolved. `/plan` is overkill for the size. The implementer needs: (1) the revised Checkpoint 2 description with the "why" framing, (2) the one-line Step 10 amendment, (3) the three anti-patterns listed above baked into the edit.
