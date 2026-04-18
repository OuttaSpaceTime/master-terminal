---
title: Make scout checkpoints pragmatic with behavior examples
status: ready-for-plan
created: 2026-04-11
---

# Scout: Pragmatic Examples in Scout Checkpoints

## Request

Rework the scout skill so each checkpoint is "less theoretical and more pragmatic with actual examples about behavior — e.g. when user does X, what do you expect."

## Target Files

- `home/dot_agents/skills/scout/SKILL.md` — checkpoint definitions (L120-198)
- `home/dot_agents/skills/scout/references/workflow.md` — (TBD, pending review)

## Problem Frame

Current checkpoint prose is rule-shaped ("walk the code", "ask 2-4 questions", "mark each gate"). What the user actually wants: checkpoint instructions that push the assistant to **surface concrete system-level impact and user-facing behavior at each step**, not recite a process.

Two flavors wanted, both woven in:

- **Impact examples** (best fit CP2–CP4): "if we change field X, serializer at `a.ts` breaks, cache key at `b.ts` goes stale, migration at `c.sql` needs a default." Concrete ripples through the system.
- **Behavior examples** (best fit CP1–CP2, CP5): "today clicking save with an empty form shows toast A; after this change we'd need to decide B or C." Concrete user-facing scenarios.

## Placement (decided)

Inline rewrite of checkpoint prose in `home/dot_agents/skills/scout/SKILL.md`. No sibling examples file — the change is shape-of-prose, not volume.

## Rewrite Plan (per checkpoint, SKILL.md)

**CP1 Problem Frame** (`SKILL.md:122-126`)
- Add verb: "Lead with one concrete *today-vs-after* behavior sketch that surfaces the first behavioral ambiguity the ticket doesn't answer."
- Litmus test in prose: a good sketch points at a real user question (e.g. "what about users on system-default?"); a bad sketch just restates the title.
- Tiny demo: `Example shape (illustrative, not prescriptive): "Today settings has no theme control; after this, users pick light/dark — but what happens for users who follow OS preference today?"`

**CP2 Code Walkthrough** (`SKILL.md:128-151`)
- Usage trace already behavior-shaped — minor touch-up: lead each interaction with `today → ?, after → ?`.
- Code trace gains *ripple order* alongside execution order:
  - Walk once in execution order for orientation.
  - Then walk in ripple order: start at the change point, follow the chain of modules whose behavior changes as a result.
  - One-sentence escape hatch: "when execution and ripple order collapse to the same path, walk it once and say so." (Risk 2 mitigation.)
- Tiny demo: `Example shape: "Touch field X at a.ts:42 → serializer at b.ts:88 produces a new key → cache read at c.ts:15 misses → test d.spec.ts:22 must update."`

**CP3 Decision Gates** (`SKILL.md:153-169`)
- Each option must carry a *concrete consequence sentence* stated as a behavior delta, not a generic tradeoff.
- Tiny demo: `Example shape: "Option A (coalesce in interceptor) → every downstream caller gets the cached response, including the admin panel that today bypasses cache. Option B (eager staleness flag) → admin panel unaffected, but every list view does one extra fetch on focus."`

**CP4 Risk and Verification** (`SKILL.md:171-177`)
- Reframe risks as *failure scenarios* — named actors, ordered events, observable outcome.
- Tiny demo: `Example shape: "If two tabs save simultaneously, tab 2's write lands on stale state from tab 1, and the user sees their change silently overwritten."`

**CP5 Mental Model** (`SKILL.md:179-198`)
- Already scenario-shaped; light touch only.
- Add: "Every scenario must name a specific file or decision from CP2 — no disconnected hypotheticals." (Current prose implies this; make it explicit.)

## Global Guardrails

- Every tiny demo prefixed with `Example shape (illustrative, not prescriptive)` to block literal copying (Risk 1 mitigation).
- No worked-out full-message examples — only shape demonstrations.
- Proportional-depth rule at `SKILL.md:75` stays intact; new CP2 verbs must not override it.

## Test Seam

The change is prose-only. Verification is empirical: run the next real scout after deploy and confirm:
1. CP1 opens with a today-vs-after sketch that surfaces a behavior ambiguity.
2. CP2 code trace walks ripple order when it diverges from execution order.
3. CP4 risks read as failure scenarios with actors and events, not rule-shaped bullets.
4. None of the tiny demos feel like literal templates.

## Now / Later / Out

- **Now:** rewrite checkpoint prose in `home/dot_agents/skills/scout/SKILL.md` per the plan above; deploy via `chezmoi -S home apply`.
- **Later:** if other checkpoint-based skills (`plan`, `diff-review`, `review`) feel similarly rule-shaped after this lands, consider porting the same verb shift.
- **Out:** sibling `references/examples.md`; any changes to `references/workflow.md`; worked full-ticket walkthrough.

> If implementation discovers work outside these boundaries, it must STOP and ask — not silently expand scope.

## Handoff

- Planning readiness: **ready**. Change is single-file, prose-only, all decisions resolved.
- Next action: run `/plan` or `/sketch` against this scout to produce the concrete diff for `SKILL.md`.
- Blockers: none.

