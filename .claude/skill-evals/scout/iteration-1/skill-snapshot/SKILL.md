---
name: scout
description: Scope a specific feature request, bug, ticket, or issue before planning or implementation. Traces affected code end-to-end, surfaces unknown unknowns, and produces a persisted scout report with an interactive guided walkthrough. Requires concrete ticket text, issue details, or an equivalent scoped request — not for generic code exploration, walkthroughs, or broad repository discovery. Trigger examples — "scout this ticket", "scope this feature before we plan", "what do we need to know before implementing #342?". Not for "how does this code work?" — use /walkthrough instead. Not for "trace why this breaks" — use /control-flow-trace instead.
---

# Feature Scout

Discover what must be learned before planning or implementation.

## Prerequisite

- Run this skill only when the user wants to work on a concrete feature, bug, ticket, or issue.
- Require the actual issue text, bug description, acceptance criteria, or an equivalent scoped request.
- If the user only wants code exploration, a control-flow walkthrough, debugging, architecture orientation, or a generic explanation, do not use this skill.

## Developer Outcome

The scout succeeds when the developer can explain the affected code paths, unknowns, and scope rationale themselves — not when the artifact is written. Give the developer better questions, better code understanding, and better decision surfaces — do not make decisions for them.

## Learning Integration

- At each checkpoint, trace the code path together so the developer follows the execution, not just the summary.
- When the developer's response reveals a gap in understanding, pause to fill it before continuing (adaptive depth).
- Checkpoint questions must target observed gaps, not generic prompts.

## Ambiguity Rule

When you encounter ambiguity — scope boundaries, design choices, API shape, data flow direction, permission models, error handling — **never silently pick a direction.** Present options with concrete tradeoffs and ask the developer to choose.

## Interactive Constraints (mandatory)
- ONE concept per message, under 200 words of prose. Pause after each step or checkpoint.
- 3-12 lines of prose per message. If more is needed, split.
- Code snippets: use fenced blocks with `lang path:start-end` info string and enclosing context.
- If developer says "skip" or "I know this," fast-forward immediately.
- For additional shared principles (scope awareness, handling disagreement), see `../references/interactive-principles.md`.

## Output Contract — Progress Footer (mandatory)

Every assistant message in this skill **must end with a progress footer as the LAST line**. No exceptions while the interactive flow is active — this includes clarifying questions, short acknowledgements, and messages that contain only code. A message without this footer is a contract violation.

**Format:**
- With steps: `Step 1/2 · Checkpoint 2/5 — Code Walkthrough & Questions: usage trace`
- Without steps: `Checkpoint 1/5 — Problem Frame`

The footer is a single line, rendered verbatim, at the very bottom of the message — nothing after it.

**Exceptions:** Omit the footer only when the developer has explicitly opted out of the interactive flow — report-only invocation, non-interactive subagent mode, or an explicit "give me the full report" request.

## Delivery Model

Two outputs, two purposes:

- **Persisted scout report** (`.claude/docs/scouts/NNN-<name>-YYYYMMDD.md`): The *artifact* — structured sections, tables, status markers, scope boundaries. What `/plan` consumes. Updated as substantive content changes.
- **Interactive chat walkthrough**: The *conversation* — questions, code traces shown to the developer, pauses for response. Builds the developer's mental model. Not persisted.

In non-interactive contexts (subagents, report-only requests), produce the report directly. The two outputs naturally collapse into one — that's fine.

Skip the chat walkthrough only when the user explicitly asks for report-only output.

## Required Deliverables

- Write scout reports to `.claude/docs/scouts` relative to the project root.
- Ensure the directory exists before writing: `mkdir -p .claude/docs/scouts`.
- Name: `.claude/docs/scouts/NNN-<scout-name>-YYYYMMDD.md`.
- Compute `NNN` as the next zero-padded 3-digit prefix in `.claude/docs/scouts`.
- Derive `<scout-name>` from the issue title when available, otherwise from ticket or branch context.
- Keep revising that same file for the lifetime of the scout.
- If the write fails (permission denied, subagent context), deliver the report inline and note that the file was not persisted.
- Return the saved file path in the final response.

## Proportional Depth

Scale depth to feature complexity — determined by execution paths, architectural boundaries crossed, and decision points, not file count.

- **Small features** (single execution path, one layer, no design decisions): Checkpoints 1-2 can be brief. May have zero questions. Expect 3-5 exchanges.
- **Medium features** (2-3 execution paths, touches 2+ layers, some design decisions): Full flow, concise. Most sections get 2-4 sentences.
- **Large features** (cross-cutting concerns, new abstractions, multiple integration points): Full depth. Split dense checkpoints into multiple steps. Expect 10+ exchanges.

A 2-file change to an auth interceptor is large. A 10-file rename is small. Judge by impact, not file count.

## Bug Scout Variant

When scouting a bug rather than a feature:

- **Skip the usage trace** (Step 1 of Checkpoint 2). There's no user interaction lifecycle to map — focus on the root-cause trace instead.
- **Expand the code trace into a root-cause trace**: Follow the execution path that produces the bug. Identify where behavior diverges from expectation. Map compounding factors.
- **Reframe decision gates as fix-strategy options**: Instead of "how should we build this?", present "how should we fix this?" with options, tradeoffs, and blast radius.
- **Test seams focus on reproduction**: How to trigger the bug in tests, not just what to test after the fix.

## Disclosure Sequencing

- Do not lead with final scope or handoff verdicts.
- Initial response: context gathered, code areas inspected, artifact path, first checkpoint.
- Lead early checkpoints with walkthroughs and questions.
- Surface final scope and readiness only after unknowns have been explored.

## Guided Session Contract

- Present the scout in 5 checkpoints that move from framing → code understanding + questions → scoping decisions → risks → handoff.
- Start each checkpoint with `Checkpoint X/5: <title>`.
- Split dense checkpoints into steps when useful.
- Pause after each step and ask whether to continue or discuss. Never auto-advance without confirmation.
- Ask 1-2 questions per step that target missing knowledge or unverified assumptions.
- Use concrete framework and codebase terminology.
- During Checkpoint 4, present one risk at a time and wait before moving on.

## Developer Expertise

- If the developer requests the full report without checkpoints, produce the artifact directly.

## Default Thoroughness

- Scout deeply, compress output to the highest-signal unknowns, decisions, and risks.
- Fewer important questions over long questionnaires.
- Tie major claims to evidence with `path:line` and a confidence label.
- Mark low-confidence, high-impact assumptions as blockers until clarified.
- If the code walkthrough reveals a hidden dependency, make it explicit even if the ticket never mentions it.
- **Every claim should be traceable**: mark each finding as **ticket-defined** (explicitly stated in the ticket/issue) or **assumed** (inferred from code or context). This distinction prevents planning landmines — every silent assumption becomes a risk.

## Checkpoints

### Checkpoint 1/5: Problem Frame

- Restate the request, known constraints, and what success seems to mean.
- **Check current branch state**: If the feature is already partially or fully scaffolded on the current branch, reframe the scout around "what's missing or next" rather than "what needs to be built from scratch." Distinguish: scaffold with mocks (needs real API integration), incomplete implementation (needs specific gaps filled), or fully implemented (may only need review). This reframing changes every downstream checkpoint.
- Identify the first missing information that could change planning direction.

### Checkpoint 2/5: Code Walkthrough & Questions

This is the core of the scout. Walk the code, surface questions as they arise, and ask blocking questions before moving on.

Split into 2-3 steps, pausing after each.

**Step 1 — Usage trace** (features only, skip for bugs): Enumerate every user-facing interaction the feature implies. Think through the full lifecycle: discover/trigger → in-progress → confirm/cancel → result → recover from mistakes. For each interaction, mark as **ticket-defined** or **assumed**. Lead with the highest-impact ambiguities — the ones where the answer changes everything downstream. Note edge cases: empty states, error/failure states, loading, undo/recovery, concurrent usage, keyboard/accessibility, permission gating.

**Step 1 — Root-cause trace** (bugs only): Follow the execution path that produces the bug. Identify where behavior diverges from expectation. Map each contributing factor with `path:line` evidence. Distinguish confirmed causes from hypotheses.

**Step 2+ — Code trace:** Walk the affected code in execution order.
- Show where current behavior lives and which adjacent modules matter.
- **Verify ticket claims against actual code** — if the ticket names a service or behavior, confirm it exists and works as described. Contradictions are high-priority findings.
- **Surface questions as you trace** — don't wait for a separate checkpoint. When you hit an ambiguity or fork point, flag it immediately ("this could work as X or Y — we'll decide in Checkpoint 3").
- Have the developer trace along — if their mental model diverges from code, pause and align.

**Required subsections after the code trace:**

- **Adjacent Code That Governs Behavior:** List existing pieces that control, constrain, or interact with the feature area — even if they won't be directly modified.
- **Extension Points:** Where the existing code provides natural hook points. Ask: "Can we hook into existing state, or do we need something new?"
- **Test Seams:** Testable entry points (component inputs, service methods, observable emissions, route params, API endpoints). For each, note the test tool or pattern that controls it. Distinguish seams that already work from seams that need creation.
- **Test Scenario Landscape:** Map acceptance criteria to happy-path scenarios. Surface edge cases and error cases from the walkthrough. Mental-model level, not detailed test specs.

**Blocking questions:** After the code trace, ask the 2-4 most important questions — the ones that could change scope, data flow, or API shape. Use forced-choice framing when possible ("Should this be A or B?"). Tie each question to a planning consequence ("if A, we need X; if B, we need Y"). Do not advance to Checkpoint 3 until blocking questions are answered or explicitly deferred.

### Checkpoint 3/5: Decision Gates

For each major ambiguity or fork point surfaced in Checkpoint 2:

- **Present as a decision with 2-3 concrete options, each with tradeoffs.** Then ask the developer to choose.
- State: what is being decided, the options, what each costs or enables, your recommendation.
- **Gate status:** Mark every gate: `[DECIDED]` — resolved during scout; `[OPEN]` — must resolve during `/plan`; `[ASSUMED]` — scout's best guess.
- **Anti-patterns:** After each gate, note what the WRONG approach would be. Example: "Do NOT create a new SelectionService — the codebase uses stateMap for all component state."
- **Pattern Alignment (mandatory):** Compare each proposed approach against established codebase patterns. Flag inconsistency as architectural risk.
- Present one gate at a time. Wait for the developer's decision.

After all gates:
- Summarize scope: `Now` (in scope), `Later` (deferred), `Out` (excluded).
- Include verbatim: "If implementation discovers work outside these boundaries, it must STOP and ask — not silently expand scope."
- Flag any gate where the developer's choice increases risk.

For bug scouts: reframe gates as **fix-strategy options** — "Option A: coalesce requests in the interceptor. Option B: eager staleness flag. Option C: fix downstream in the directive."

### Checkpoint 4/5: Risk and Verification

- Walk one major risk or compatibility concern at a time.
- For each: what could go wrong, how likely, blast radius, how to verify it won't happen.
- **Architectural Risk:** When an implementation choice violates codebase norms, flag it even if technically sound.
- **In-Flight Changes:** Check whether other branches touch the affected files. Concurrent modifications are merge risk.
- If a risk invalidates a Checkpoint 3 decision, say so.

### Checkpoint 5/5: Mental Model & Handoff

An iterative stress test that builds the developer's mental model of the change until they can reason about it independently. The developer may say "done", "enough", or "skip" at any point to exit — immediately move to the handoff summary when they do.

**Mental-model loop (repeat until solid or developer exits):**

1. Pose ONE concrete scenario question: "What would you expect to happen if...?" Pick scenarios that probe the edges — error paths, race conditions, boundary interactions, state transitions, the spots where wrong assumptions cause real bugs. Start with the highest-risk area from Checkpoint 4.
2. Listen to the developer's answer. If their model is accurate, confirm briefly and move to the next scenario. If it has a gap or misconception, walk through the relevant code path together until the gap is filled — then re-ask or pose a follow-up that tests the corrected understanding.
3. Escalate scenario complexity as the developer's model solidifies — start with "what happens when X?" and progress toward "what happens when X *while* Y is also in flight?" or "where would you look if Z broke after this lands?"
4. Stop the loop when: the developer exits, OR the developer answers 2-3 consecutive scenarios accurately including at least one cross-cutting scenario. When stopping on model strength, say so: "Your model covers the critical paths — moving to handoff."

**Question design principles:**
- Ground every question in code and decisions from earlier checkpoints — no hypotheticals disconnected from the actual change.
- Prefer forced-prediction questions ("what value would `foo` hold at this point?") over recall questions ("what did we decide about X?").
- One question per message. Keep it short.

**After the loop — Handoff summary:**
- State whether planning is ready, conditionally ready, or blocked.
- Summarize: minimal `Now` scope, open blockers, next action.
- Verify the scout produced what `/plan` needs: (1) clear `Now/Later/Out` boundaries, (2) all blocking ambiguities resolved or accepted as risks, (3) affected files and test seams identified.

## Workflow

For the detailed step-by-step workflow and walkthrough evidence requirements, see `references/workflow.md`.
