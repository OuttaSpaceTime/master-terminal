---
name: plan
description: >
  Produce an implementation plan with file and test impact mapping, execution-flow deltas,
  compatibility assessment, and draft diffs. Use when a developer has a concrete feature,
  bug, or ticket and needs a sequenced execution strategy before coding. Distinct from
  `/sketch` for small well-understood changes and `/scout` for exploratory discovery.
---

# Implementation Plan With Diffs

Turn understanding into an implementation strategy.
Keep planning compressive, not exploratory: inherit and validate prior discovery when it exists, or perform only the minimum discovery needed to plan safely when it does not.

## Plan Artifact Purpose

The plan artifact must be self-contained enough that an implementation agent can follow it without asking clarifying questions. Every constraint, scope boundary, and decision must be explicit. Ambiguity in the plan becomes bugs in the implementation.

## Core Stance

- `/plan` bridges understanding to execution — it does not explore, it sequences.
- Scout exists? Inherit it, validate against code, compress into implementation steps. Never redo scout work.
- No scout? Run bounded minimal discovery (max 10-15 files). If ambiguity remains, stop and recommend `/scout`.
- Produce draft diffs only after understanding is established and confidence is high.
- Align every step to the repository's existing architecture, extension points, and local patterns.
- Before planning new work, assess whether the requested capability already exists. If it does, reframe the plan around the delta — what's actually missing — rather than proposing to rebuild existing infrastructure.
- Shape the plan so the developer finishes with a clear mental model of what changes, how the loop closes, and how completion is verified.

## Interactive Constraints (mandatory)
- ONE concept per message, under 200 words of prose. Pause after each step or checkpoint.
- 3-12 lines of prose per message. If more is needed, split.
- Code snippets: use fenced blocks with `lang path:start-end` info string and enclosing context.
- If developer says "skip" or "I know this," fast-forward immediately.
- If the developer requests the full plan without checkpoints, produce the artifact directly.
- For additional shared principles (scope awareness, handling disagreement), see `references/interactive-principles.md`.

## Output Contract — Progress Footer (mandatory)

Every assistant message in this skill **must end with a progress footer as the LAST line**. No exceptions while the interactive flow is active — this includes clarifying questions, short acknowledgements, and messages that contain only code. A message without this footer is a contract violation.

**Format:**
- With steps: `Step 1/2 · Checkpoint 2/3 — Loop Closure: trace trigger to completion`
- Without steps: `Checkpoint 1/3 — Mental Model`

The footer is a single line, rendered verbatim, at the very bottom of the message — nothing after it.

**Exceptions:** Omit the footer only when the developer has explicitly opted out of the interactive flow — report-only invocation, non-interactive subagent mode, or an explicit "give me the full plan" request.

## Developer Outcome

- The developer should finish with a clear mental model of what changes architecturally and why.
- Completion criteria must distinguish "code was written" from "the task is actually finished."
- Checkpoints sharpen reasoning — keep them generative, not bureaucratic.
- Success test: the developer could implement without referring back to the artifact. The understanding is internalized; the artifact is backup.

## Interactive Planning Flow

Plan always runs interactively. It adapts how much discovery it does, but it does not expose named modes.

- If a matching scout exists for the same feature, issue, or branch, inherit it as the primary source and validate only what matters for implementation accuracy.
- If no scout exists, run a bounded discovery pass first: read no more than 10-15 files.
- Use the smallest amount of discovery needed to plan safely: entrypoint, execution flow, architectural boundaries, local patterns, high-confidence touchpoints, major unknowns.
- After discovery, classify each ambiguity found and choose one of three outcomes:
  1. **Resolved by discovery** — the search answered the question. State what was found and proceed.
  2. **1-2 isolated ambiguities remain** — present options with tradeoffs and ask the developer to decide. Do not punt to `/scout` for questions you can frame clearly.
  3. **Broad ambiguity remains** — multiple unknowns that interact or cascade (e.g., unknown API contract that reshapes service layer, auth, and test strategy). Stop and recommend `/scout`, specifying what the scout should resolve.
- The classification must appear in the **Discovery Assessment** section of the output (see Output Template). Skipping this reasoning is not allowed — even when discovery resolves all ambiguities, state that explicitly.
- Do not silently expand into a fully exploratory scout.

**Minimal discovery exit criteria** -- all must be satisfied before proceeding to planning:

1. Entrypoint identified (the file/function where the change starts)
2. 2-3 key execution paths traced from trigger to outcome
3. Major architectural boundaries found (service layers, module edges, API contracts)
4. Local coding patterns observed (naming, structure, test style in the affected area)
5. No material unknowns that would reshape the design

If any item is not satisfied, either resolve it within the 10-15 file budget or stop and recommend `/scout`.

## Confidence Gate For Draft Diffs

Only produce draft diffs when **every** check passes:

1. **Current execution flow traced end-to-end** -- from trigger through service/domain logic to persistence/UI outcome, with no gaps filled by assumption
2. **New execution flow traced end-to-end** -- the planned path from the same trigger through modified logic to the new outcome, step by step
3. **All impacted files read and validated** -- every file listed in File Impact has been opened and inspected, not just inferred from names or imports
4. **Syntax and patterns match existing code** -- draft diffs use the actual import style, naming conventions, DI patterns, and test structure found in the affected files
5. **API contract is known** -- the plan depends on a concrete, confirmed API shape. If the API contract is unknown or unconfirmed, this check fails regardless of whether the plan introduces breaking changes. Distinguish: (a) known contract with breaking change → document mitigation; (b) unknown contract → diffs cannot be drafted, state what must be resolved first
6. **Test scenarios mapped to requirements with mocking strategy identified** -- each requirement has concrete test cases (precondition → action → expected outcome), test type rationale, and mocking approach documented

If any check fails: provide the plan without draft diffs, state which checks failed and why, and specify what must be resolved first (additional reading, developer decision, or full `/scout`).

## Guided Checkpoints

Present three checkpoints interactively, each as `Checkpoint X/3: <title>`. After each, ask: "Continue or discuss further?" Respect skip requests.

1. **Mental Model** — Restate objective and planning mode. **Ask the developer to predict** what files or layers will change and why — before you reveal the plan's impact map. Listen for gaps or wrong assumptions, fill them, then confirm against what the plan actually covers. Surface any ambiguous planning question.
2. **Loop Closure** — Walk the execution flow trigger-to-completion. Make the developer trace along. Make explicit: what starts the work, what state changes, what downstream outcome proves the loop closed. Finish the checkpoint by asking the developer — in their own framing — *"what would you expect to be tested to prove this loop closes?"* Thinking through what needs testing **is** loop-closure reasoning: if the developer can't say what proves it's done, they haven't closed the loop. Capture their expectations conversationally — **do NOT add a new section to the plan artifact** — and fold them into the Testing Strategy table when Step 10 runs. Surface gaps the developer missed as conversational additions (*"adding X because without it the trigger→outcome path isn't verified"*); never silently overwrite the developer's framing. Run this sub-step even when a scout exists: scout's Test Scenario Landscape is planner-inferred and does not substitute for dev-stated expectations.
3. **Finish Signals** — Have the developer articulate finish signals first. Use concrete signals: observable behavior, passing tests, clean checks. State whether draft diffs are ready or withheld.

## Workflow Steps

### 1. Gather Inputs and Select Planning Flow

- Require an issue, brief, or equivalent source input.
- If a scout document already exists for this feature, inherit it as the primary source.
- If no scout exists, perform the minimal bounded discovery needed to plan safely.
- Preserve source requirements verbatim in the output.
- Mark whether the plan is scout-backed or discovery-based near the top of the plan.

### 2. Load Existing Understanding

If using a scout-backed flow:

- extract decided items, assumptions, blockers, and scope boundaries from the scout
- inherit the current-flow understanding unless code inspection disproves it
- inherit resolved questions instead of asking them again

If using a discovery-based flow:

- record the initial constraints, non-goals, and missing inputs
- state that only minimal discovery was performed

### 3. Read the Real Codebase and Validate the Shape

- Inspect the real files before planning.
- Never invent file structure, APIs, or extension points.
- Validate the relevant execution path, architectural boundaries, and local patterns.
- Mark uncertain areas explicitly with confidence labels.

### 4. Reconstruct the Execution Flow Early

- Build the current execution flow as one of the first planning steps.
- If the change is already partially designed, outline the expected new execution flow as well.
- Trace in runtime order: entrypoint, coordinator/container, domain/service logic, persistence/integration boundary, tests/verification seams.
- Separate: known facts, inferred assumptions, unresolved unknowns.

### 5. Assess Discovery and Decide Whether Planning Can Continue

This step produces the **Discovery Assessment** section in the output when no scout exists, and it must appear before any implementation detail.

- List each ambiguity found during discovery.
- Classify each as: **resolved** (discovery answered it), **isolated** (remains but can be framed as options), or **broad** (interacts with other unknowns, cascades).
- State the chosen path and why:
  - All resolved → proceed to planning, state what was found
  - 1-2 isolated → present options with tradeoffs, ask the developer
  - Broad → stop, recommend `/scout`, specify what it should resolve
- If understanding is sufficient, continue into implementation planning.

### 6. Set Objective and Scope Guardrails

- Start with a concise objective statement.
- In a scout-backed flow, inherit scope boundaries from the scout and restate only what matters for implementation.
- In a discovery-based flow, define the smallest safe in-scope and out-of-scope boundary supported by the minimal discovery pass.
- Separate confirmed decisions from assumptions.
- Mark each decision gate with a status: `[DECIDED]` (resolved, proceed), `[OPEN]` (unresolved, implementation must not proceed past this point without developer input), or `[ASSUMED]` (assumed but not confirmed, flag if implementation reveals it's wrong). An implementation agent encountering an `[OPEN]` gate must stop and ask. It must not silently resolve the decision.

### 7. Build Impact Inventory

List impacted files, modules, integrations, tests, and checks with: current responsibility, why impacted, rough change intent, risk and confidence, impact type (create/modify/delete/reference). Walk the impact map in interaction order when possible, not alphabetically.

### 8. Define Before, After, Flow Delta, and Loop Closure

- Summarize current behavior and planned behavior.
- Describe current and new execution flow steps.
- Explicitly list delta points.
- Make explicit how the planned flow closes the loop: what starts the work, what state changes, what downstream outcome proves the loop closed, and what final state marks successful completion.

### 9. Draft Implementation Steps

Concise numbered steps in execution order: one action per step, aligned to existing architecture and local patterns, no low-level tutorial text, no speculative steps that depend on unresolved blockers. For each step, note which test scenario(s) from Step 10 validate it — the developer should be able to trace any step to its verification.

### 10. Define Testing Strategy

- Map each requirement and each major risk to automated or manual verification.
- **Incorporate developer expectations**: Every expectation the developer voiced during Checkpoint 2's test-expectations sub-step becomes at least one row in the Testing Strategy table, phrased close to the dev's framing. Planner-added gap rows (coverage the dev didn't mention but the loop requires) are allowed and encouraged, but the table itself does not label sources — the distinction lives in the conversation. Never silently rewrite the dev's framing to match planner phrasing.
- **Scenario breakdown**: For each requirement, enumerate concrete test cases as precondition → action → expected outcome. Be specific about inputs and assertions, not just "test that X works."
- **Test type rationale**: For each test, state unit/integration/e2e and why — what needs isolation, what needs real wiring.
- **Mocking strategy**: For each test, state what gets mocked, what stays real, and which existing test utilities or helpers from the codebase to use.
- **Pattern reference**: Point to an existing spec file in the codebase that serves as the template for each new test.
- Call out existing tests to update and new tests to add.
- Provide concrete verification commands the implementer should run.

### 11. Evaluate Compatibility and Failure Risk (when relevant)

Include this section only when the change modifies shared interfaces, data schemas, API contracts, or crosses architectural boundaries. For additive changes within a single component or module, omit entirely.

When included: assess compatibility risk for data/schema evolution, API/contract behavior, background/async processing, outbound communication, external integrations. Mark each: compatible, conditionally compatible, or breaking. List likely failure modes with how they would be triggered.

### 12. Evaluate Confidence Gate (Required Section)

Produce the **Confidence Gate** section in the output. Evaluate each of the 6 checks from the "Confidence Gate For Draft Diffs" section above. For each check, state PASS or FAIL with a one-line evidence note. This section must appear in the plan even when all checks pass — it makes the reasoning auditable.

### 13. Draft Executable Diffs Only When Confidence Is High

- Provide draft git-style diffs per impacted file only if every confidence gate check passed.
- Use actual syntax from inspected files. Include 2-3 lines of context.
- Copy surrounding context lines verbatim from the file — do not simplify, shorten, or paraphrase existing code. If a line has a conditional expression, attribute, or flag, reproduce it exactly.
- Label clearly as draft plan diffs, not applied changes.
- If confidence is not high enough, explain why diffs were withheld.

### 14. Confirm Readiness and Finish Signals

- State finish signals explicitly. Each finish signal must be a command that returns pass/fail or a specific observable state change — not vague descriptions like "feature works." Example: "User clicks Save -> API returns 200 -> item appears in list" not just "saving works."
- End with unresolved blockers and open questions.
- Distinguish: decided items, assumptions, blockers requiring clarification.

### 15. Write Report to File

- Write the complete plan to `.claude/docs/plans/plan-YYYYMMDD-HHMMSS.md`.
- Create the directory first: `mkdir -p .claude/docs/plans`.
- If the write fails (permission denied, subagent context), deliver the plan inline and note that the file was not persisted. The plan content is the deliverable — the file is for convenience.
- Do not output plan content only in chat without attempting to save the file.

## Output Template

For the full output template with table column headers, load `references/workflow.md` before producing the final artifact.

## Proportional Depth

Scale the plan to feature complexity. Complexity is determined by the number of execution paths, architectural boundaries crossed, and decision points — not file count alone.

A 2-file change to an auth interceptor is large. A 10-file rename is small. Judge by impact, not file count.

- **Small changes** (single execution path, no design decisions, confidence obviously high): **Use the compact template** below. The plan is a short document, not 16 sections.
- **Medium changes** (2-3 execution paths, touches 2+ layers, some design decisions): Full template with all always-present sections.
- **Large changes** (cross-cutting concerns, new abstractions, multiple integration points): Full template plus conditional sections as needed.

### Complexity Reclassification

If discovery reveals that the initial classification is wrong — e.g., the prompt says "simple 3-file change" but discovery finds a Postgres enum migration, multiple views, and a new controller — upgrade the classification explicitly before continuing. State: "Reclassifying from small to medium: [reason]." Then switch to the appropriate template. Do not use the compact template while producing medium-depth output.

### Compact Template (small changes only)

Use this template when the change is genuinely small after discovery:

1. Planning Flow + TL;DR (combined, 2-3 sentences)
2. File Impact (table)
3. Implementation Steps (numbered)
4. Testing Strategy (table)
5. Confidence Gate (inline: "All 6 checks pass — [one-line reason]" when the answer is obvious)
6. Draft Diffs
7. Open Questions (only if any exist)

Omit: separate Source Requirements, Objective, Scope Guardrails, Before/After Execution Flow, Finish Signals, Discovery Assessment. These add structure overhead without value for single-path additive changes.

### Full Template (medium+ changes)

**Always-present sections** (core of every medium+ plan):
1. Report Location
2. Planning Flow
3. Discovery Assessment (when no scout exists) — ambiguities found, classification, path chosen and why
4. TL;DR
5. Source Requirements
6. Objective
7. Scope Guardrails — fold Known/Inferred/Unknown into here as confidence-labeled bullets rather than a separate section
8. File Impact (table)
9. Affected Tests / Checks (table)
10. Before / After and Execution Flow — combine current vs new behavior and flow deltas into one section
11. Implementation Steps — numbered, one action per step, each noting test scenarios
12. Testing Strategy (table)
13. Finish Signals — fold Loop Closure into here (trigger, completion signal, failure signal, verification commands, "still unfinished if")
14. Confidence Gate — evaluate each of the 6 checks, state pass/fail with evidence
15. Draft Diffs (or explanation if withheld — must follow Confidence Gate)
16. Open Questions / Blockers

**Include only when relevant** (omit entirely if not applicable — do not write "N/A" rows or "not applicable" placeholders):
- **Compatibility and Failure Risk** — only when the change modifies shared interfaces, data schemas, API contracts, or crosses architectural boundaries
- **Potential Issues and Reproduction** — only when there are non-obvious failure modes worth documenting
- **Implementation Constraints** — only when there are genuine DO NOT / MUST / STOP rules beyond standard project conventions
- **Architectural Change Model** — only when the change introduces new abstractions, patterns, or architectural boundaries (not when it follows an existing pattern)

## Required Deliverable

Always save the final plan to `.claude/docs/plans/plan-YYYYMMDD-HHMMSS.md` (create the directory with `mkdir -p` if needed). Return the saved file path in the final response.

## Parallel Discovery (optional)

For shared protocol mechanics (complexity gate, spawn protocol, synthesis, on-demand triggers), see `references/parallel-agents.md`. For this skill's agent roster, return format schemas, and critique agent protocol, see `references/parallel-discovery.md`.

**Activation:** Discovery-based medium+ tasks spawn upfront agents automatically. Scout-backed flows skip upfront agents by default because the scout already did discovery. Override with `--parallel` (force agents) or `--no-parallel` (force single-pass).

**Upfront agent roster (discovery-based medium+ tasks):**
- **Entrypoint flow tracer** — trace trigger-to-outcome execution path, map architectural boundaries
- **Pattern reference reader** — read the most similar existing feature for conventions, naming, structure, test style
- **Test infrastructure scanner** — check test helpers, patterns, existing coverage, framework-specific test utilities

**Phase placement:** Agents run during Steps 1-5 (discovery phase). Synthesis feeds Step 6+ (planning phase). If the project has a verification suite, run gate checks in parallel with upfront agents. The 10-15 file cap for the discovery-based main thread applies only to the main thread — upfront agents operate within their own bounded mandate.

**Scope at spawn time:** If scope guardrails have not yet been set (Step 6 runs after discovery), pass the raw feature request as a tentative scope proxy in agent payloads.

**Critique agent:** Fires after Step 13 (Draft Diffs), before Step 14 (Readiness and Finish Signals). Receives the complete plan and draft diffs (the in-memory artifact, not yet written to file). Returns: missed implementation steps, ordering bugs, untested paths, scope creep beyond guardrails. Valid ordering bugs may trigger a diff revision before Step 14. All other valid findings are appended to Open Questions / Blockers in Step 14.

**Scout-backed exception:** If the inherited scout is stale or the plan needs to validate specific claims against current code, upfront agents may spawn on a case-by-case basis. Announce the reason.

**Read `references/parallel-discovery.md` before spawning** — it contains the return format schemas required for each agent's spawn payload.

## Guardrails

**Output quality:** Target 5-10 minute review. Bullets and tables over prose. Only actionable technical detail. Confidence labels on uncertain items. Minimum planning surface needed to guide implementation.

**Behavioral constraints:**
- Plan only — do not implement.
- Read files before drafting steps or diffs. Use exact existing syntax in draft diffs.
- Never turn assumptions into decisions without calling them out.
- Never produce draft diffs when understanding is not yet established (see Confidence Gate).
- If minimal discovery reveals broad ambiguity, stop and recommend `/scout`.
