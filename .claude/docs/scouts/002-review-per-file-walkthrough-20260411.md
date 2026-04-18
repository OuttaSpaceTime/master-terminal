# Scout 002 — Per-File Review Walkthrough

**Date:** 2026-04-11
**Target skills:** `home/dot_agents/skills/review/SKILL.md`, `home/dot_agents/skills/diff-review/SKILL.md`
**Request (original):** Add a per-file review flow to /review with a tracked Progress Tracker and interactive per-file stepping.
**Request (after pivot):** Align /review and /diff-review with their natural roles. /diff-review owns code comprehension with hunk-level per-file stepping. /review owns findings-walkthrough and merge readiness, presenting one finding per step with inline evidence excerpts — no code re-walk.

## Scope Pivot (locked mid-scout)

Initial direction was to port diff-review's per-file tracker into /review, creating a per-file walk inside /review itself. Mid-scout the developer surfaced the real doubt: **the /review reviewer is the developer who wrote the code**. Re-walking code they just authored is low-value. /diff-review already owns comprehension. Cleaner split:

- **`/diff-review`** — code comprehension. Per-file walkthrough with hunk-level step granularity, Progress Tracker, invariants surfaced inline.
- **`/review`** — merge readiness and findings. One finding per step, evidence excerpts inline, severity + verdict. No per-file code walk.

The chain is already documented: `diff-review/SKILL.md:281` points at `/review` for escalation to severity-rated findings.

## Problem Frame

Two concrete problems this change solves:

1. **Large files in /diff-review.** Today `diff-review/SKILL.md:183` walks each significant file or logical group as one message. A file with five hunks blows the 3-12 line message budget; reviewer has to scroll through a wall of diff. Hunk-per-step granularity fixes this.
2. **/review's current code-walkthrough duplication.** /review's Checkpoint 3 (Affected Code Walkthrough) exists to build a reviewer mental model — but the reviewer IS the author. The walk is ceremony without understanding gain. Pivoting /review to a findings-walkthrough sharpens its job.

The change also prepends a **flow map** (general execution-flow-changes overview) to /diff-review's CP1 so developers get a cross-file mental model before diving into per-file hunks. The developer-stated purpose of this section: *"establish the correct high-level mental model of the changes and their effects on control flow."*

## Files Touched

| File | Change |
|---|---|
| `home/dot_agents/skills/diff-review/SKILL.md` | Hunk-level step granularity in CP2; prepend flow map section to CP1; minor footer format update for hunk index; retain self-contained-first walk order (reverted from earlier risk-first decision) |
| `home/dot_agents/skills/review/SKILL.md` | Collapse CP3 (Affected Code Walkthrough) — lightweight hot-spot version only, no exhaustive file walk; restructure CP5 (Findings) as the findings walkthrough with one-finding-per-step and evidence excerpts; add finding status column; update chain to suggest `/diff-review` first when code comprehension is needed |
| `home/dot_agents/skills/review/references/workflow.md` | Drop the per-file review plan expansion (§6) that was being planned; update findings section for the new rhythm |

Scope is skill-text only. No runtime code, no tests. Validation: `chezmoi -S home diff` and manual dry-runs of both skills on a real branch.

## Affected Sections

**diff-review:**
- `SKILL.md:38-44` — Progress Footer (hunk index addition)
- `SKILL.md:119-144` — Notes File / Progress Tracker (hunk sub-status)
- `SKILL.md:150-162` — CP1 Diff Overview (prepend flow map step)
- `SKILL.md:165-194` — CP2 Change Walkthrough (hunk-per-step rhythm)
- `SKILL.md:192-194` — walk order (retain self-contained-first)

**review:**
- `SKILL.md:38-48` — Progress Footer (finding index addition)
- `SKILL.md:71-81` — Required Deliverables (finding status column)
- `SKILL.md:83-102` — Guided Session Contract (suggest /diff-review chain)
- `SKILL.md:134-161` — CP3/4/5 checkpoint restructure
- `workflow.md:72-76` — Per-file review plan (simplified, no interactive loop)
- `workflow.md:172-184` — Finalize Findings and Verdict (new rhythm)

## Decision Gates

### Gate α — Hunk-per-step granularity for /diff-review `[DECIDED → yes]`
- Each hunk of a changed file becomes its own step. Multi-hunk files walk across multiple messages with the file context carried forward.
- **Footer format:** `Step 2a/5 · Checkpoint 2/4 — src/foo.ts: hunk 1/3` or equivalent. The file index owns the main counter; the hunk index is a sub-counter rendered in the trailing descriptor.
- **Single-hunk files** collapse to a normal step (no `hunk 1/1` noise).
- **Per-hunk content.** Each hunk message carries: the hunk itself, a one-to-three sentence behavioral summary, adjacent governors **only if this hunk needs them** (pulled in inline, soft-split rule applies). Invariants and concerns still surface in their own messages per file, not per hunk — they are file-level observations, not hunk-level.

### Gate β — /diff-review walk order `[DECIDED → self-contained-first]`
- Reverted from the earlier risk-first decision that was contingent on /review sharing this rhythm. Under Path B, /diff-review is a pure comprehension tool. Building understanding from leaves inward (fewest imports from other changed files) is correct for comprehension. `diff-review/SKILL.md:192-194` stays.

### Gate γ — Flow map in /diff-review CP1 `[DECIDED → yes, as a table]`
- Prepend an **Execution Flow Changes** step to CP1, before the Diff Overview table. Content: which paths are now different, what crosses new boundaries, which control-flow branches are new or removed. Dense table form: `Phase | Files | What crosses the boundary`. No code excerpts — CP2 owns code.
- Purpose (developer-stated): establish the high-level mental model and control-flow effects before drilling into per-file hunks.
- Skip rule: trivial diffs and single-layer small diffs collapse the flow map to a one-line summary.

### Gate δ — /review checkpoint restructure `[DECIDED → collapse CP3, expand CP5]`
- **CP1** Change Intent + Entry Flow — unchanged.
- Gate Checks — unchanged.
- **CP2** Actual Execution Flow — unchanged (reviewer-side mental model, orthogonal to whether they authored the code).
- **CP3** Critical Hot Spots — lightweight replacement for the old "Affected Code Walkthrough". Walks only the one or two highest-risk hot spots (auth, data mutation, shared libs) to ground the findings. Not an exhaustive per-file walk. May be skipped entirely if the developer has already run /diff-review or explicitly declines.
- **CP4** Assumptions and Review Questions — unchanged purpose.
- **CP5** Findings Walkthrough — the core of the skill. One finding per step. Each step: finding statement + severity + evidence code excerpt + reasoning chain + developer response (accepted / discussed / developer-accepted risk / dismissed). Status column in the artifact tracks which findings have been discussed.
- **CP6** Tests, QA, Compatibility, Verdict — unchanged.
- **Stays at 6 checkpoints.** Collapsing to 5 was considered and rejected — keeping 6 preserves skill-to-skill consistency and doesn't force renumbering across skill references.

### Gate ε — /review findings status tracking `[DECIDED → yes, status column]`
- Findings table in the artifact gains a `Status` column: `pending | walked | accepted-risk | dismissed | blocker-open`. Updated after each finding is discussed (live write, same carve-out rationale as the earlier Progress Tracker — findings-change-only rule keeps the rest of the artifact minimal-churn).
- **Pre-verdict check:** CP6 cannot declare merge-ready while any finding is `pending` or `blocker-open`.
- **Resume protocol (lightweight port from diff-review):** before walking any finding, read the findings table. Only walk `pending` findings. This is the single source of truth for where the session left off.
- **Interactive exploration during a finding walk (developer-requested refinement):** while a finding is being discussed, the developer may ask for code outlines, explanations of adjacent symbols, or data-flow traces. These are exploration — they do not advance the finding counter. Footer stays fixed on the current finding. Same discussion-pause semantics as /diff-review's per-hunk rhythm. Return phrasing on resume: *"Back to finding X — ready to advance, or more to discuss?"*

### Gate ζ — Chain hint from /review to /diff-review `[DECIDED → yes]`
- /review's CP1 explicitly asks whether the developer wants to run /diff-review first for code comprehension. If yes, /review pauses and chains. If no, /review continues with its own CP2 (execution flow) and CP3 (hot spots), grounding the findings itself.
- Added to `review/SKILL.md` chain documentation.

### Gate η — Interactive-principles tension (from Path A, carried forward)
- Still applies to /diff-review's per-hunk rhythm. Soft split rule: if a hunk message exceeds 3-12 lines, split into diff → behavior. Hard rule: each **concern** (diff-review's analog of review's finding) is still its own message. These rules were already agreed under Path A and port cleanly into the /diff-review-only scope.

## Deprecated Decisions (from Path A, for audit)

The following decisions from Path A no longer apply under Path B:

- ~~Gate A (per-file loop in /review spanning CP3 and CP5)~~ — /review no longer has a per-file loop.
- ~~Gate B walk order for /review~~ — /review no longer walks files.
- ~~Gate C `✅ reviewed` semantics~~ — /review tracks findings, not file status.
- ~~Gate D tracker-update carve-out in /review~~ — applies only to /diff-review now.
- ~~Gate F CP2 flow-map compression in /review~~ — /review CP2 stays as-is.
- ~~Gate G cross-file finding placement rule~~ — no longer needed; findings are findings, not file-attached.
- ~~Gate J adjacent governors per-file inline rule in /review~~ — applies only to /diff-review.
- ~~R1 rhythm friction / low-risk batching / R5 seed loss~~ — dissolved by the pivot.

## Scope (locked under Path B)

**Now:**
- `diff-review/SKILL.md` — hunk-per-step granularity in CP2 (Gate α); flow map step prepended to CP1 as a table (Gate γ); footer format update for hunk sub-counter; Progress Tracker schema unchanged (still per-file) but status-marking rule adjusted so a file is `✅` only after all its hunks are walked; retain self-contained-first walk order (Gate β).
- `review/SKILL.md` — collapse CP3 to "Critical Hot Spots" (optional, skippable when the developer ran /diff-review first); restructure CP5 as Findings Walkthrough with one-finding-per-step, evidence excerpts inline, status column, resume protocol (Gate δ, ε); add Gate ζ chain hint to CP1.
- `review/references/workflow.md` — simplify §6 per-file review plan back to a short planning aid; update §12 finalize-findings to describe the walkthrough rhythm.

**Later:**
- Port hunk-level granularity upward into /scout and /plan if it proves useful.
- Consider shared `references/per-file-walkthrough.md` to DRY the diff-review contract if more skills adopt it.

**Out:**
- Per-file walkthrough in /review.
- Progress Tracker for files inside /review artifact.
- Any changes to `references/interactive-principles.md` beyond minor pointers.
- Tool-level changes, MR-API integration, changes to any other interactive skill.

> If implementation discovers work outside these boundaries, it must STOP and ask — not silently expand scope.

## Risks

- **R1 rhythm friction** `[DISSOLVED by pivot]` — /review no longer walks every file.
- **R2 double walkthrough** `[DISSOLVED by pivot]` — /review CP2 flow map and CP3 hot spots no longer overlap /diff-review's per-file walk.
- **R3 progress footer overload** `[MITIGATED — sub-counter stays at 2 levels]` — diff-review footer: `Step M/N · Checkpoint 2/4 — file.ts: hunk K/L`. File index owns the counter slot, hunk index lives in the descriptor.
- **R4 artifact churn** `[MITIGATED]` — /review gains a finding-status carve-out (same pattern as diff-review's Progress Tracker carve-out); everything else remains findings-change-only.
- **R5 cross-file seed loss** `[DISSOLVED by pivot]` — no batching in /review; /diff-review's walk order is self-contained-first which already handles cross-file dependency order.
- **R6 (new). Split is wrong when the reviewer is NOT the author.** The pivot assumes `/review` runs on code the developer wrote. If a teammate runs /review on someone else's PR, they genuinely need the code walkthrough. Mitigation: Gate ζ's chain hint explicitly offers /diff-review first. If the reviewer declines /diff-review and runs /review cold on unfamiliar code, /review's CP2 (execution flow) and CP3 (hot spots) still provide grounding — just less thoroughly than the old per-file walk. Acceptable trade: most /review runs are self-review; external review has a documented escalation path.
- **R7 (new). Findings-walkthrough makes /review hard to use non-interactively.** The existing skill supports report-only mode for subagents and trivial diffs. A one-finding-per-step rhythm is interactive by nature. Mitigation: report-only mode compresses all findings into a single findings-table section, same as today — the new rhythm applies only in the interactive path. Add an explicit "non-interactive path preserves the current rollup output" rule.

## Handoff

**Readiness:** Ready for `/plan`.

**Minimal Now scope recap:**
1. `/diff-review` gains hunk-per-step granularity (Gate α), flow-map step prepended to CP1 as a table (Gate γ), self-contained-first walk order retained (Gate β).
2. `/review` CP3 collapses to optional "Critical Hot Spots"; CP5 Findings restructures as one-finding-per-step with evidence excerpts; finding status column tracks `pending | walked | accepted-risk | dismissed | blocker-open`; Gate ε pre-verdict check blocks merge while any finding is `pending | blocker-open`.
3. Gate ζ adds a CP1 chain hint from /review to /diff-review for code comprehension.
4. Interactive exploration during a finding walk does not advance the counter — same discussion-pause semantics as diff-review's per-hunk rhythm.

**Open blockers:** none.

**Deferred risks:** R6 (non-author reviewer) is acceptable under the chain hint. R7 (non-interactive mode) mitigated by preserving the existing rollup output path.

**Next action:** run `/plan` with this scout as input to produce the implementation plan and diff set.

**Mental model verified on:**
- Scenario 1 (interruption during hunk walk) — correct on the first try.
- Scenario 2 (findings verdict gating + resume) — corrected after one Path A carry-over, re-asked and answered correctly.
- Developer added one refinement (interactive exploration during finding walk) that is now part of Gate ε.
