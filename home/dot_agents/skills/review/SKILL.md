---
name: review
description: Code review current changes against mainline — judgment-only. Produces severity-rated findings on a diff, with the chained `/diff-review` providing the code walkthrough and comprehension grounding. Covers bugs, regressions, correctness, acceptance-criteria coverage, test gaps, architecture fit, framework best practices, resilience, security, change minimality, locality of definition, and backward compatibility. Produces a persisted review artifact plus guided interactive findings walkthrough. Use when asked to review a pull request, review staged or unstaged changes, review an implementation, check merge readiness, or review code before landing. Do NOT use for general code exploration, architecture questions without a concrete diff, or test-only runs — and use `/diff-review` instead when the goal is to understand what the diff does.
---

# Code Review

Understand the change before judging it.
Favor generative review work first: trace the affected code, form hypotheses, expose assumptions, and only then finalize findings and verdicts.

For detailed workflow steps, walkthrough requirements, and MR comment modeling, see `references/workflow.md`

## Developer Outcome

- Sharpen the developer's judgment, not replace it. The review succeeds when the developer can articulate the change's architecture fit, the real risks, and what adjacent code still governs behavior — not when the findings list is delivered.
- Leave the developer with a clearer model of how the change fits or conflicts with existing architecture, style, and execution flow.

## Core Stance

- Start generative: ensure the change is understood first (chain to `/diff-review` by default; rely on agent synthesis + diff reading when standalone), then map adjacent dependencies and invariants, surface open questions, and only then emit findings.
- Review both changed code and nearby unaffected code when that nearby code governs behavior, contracts, rollback paths, or testability — but the comprehension walk happens in `/diff-review`, not here.
- Primary review lenses: change minimality (no broader or more abstract than the problem requires), locality of definition (helpers and types stay near their only call sites unless reuse is concrete), and alignment with existing architecture and local code style.
- Prioritize correctness, risk, and maintainability over stylistic preference.

## Cross-Cutting Concerns

- For shared-layer changes (middleware / guards / interceptors / base classes / shared services), the downstream-path trace is owned by `/diff-review` (its CP2 cross-cutting rule). When `/review` runs standalone, surface the downstream-consumer assumption explicitly in CP2 (Assumptions) instead — name at least one consumer whose contract the change touches.
- Verify that the change does not silently alter behavior for consumers that were not part of the stated intent. Findings that catch unintended consumer impact are high-severity by default.

## Interactive Constraints (mandatory)
- ONE concept per message, under 200 words of prose. Pause after each step or checkpoint.
- 3-12 lines of prose per message. If more is needed, split.
- Code snippets: use fenced blocks with `lang path:start-end` info string and enclosing context.
- If developer says "skip" or "I know this," fast-forward immediately.
- Present findings one at a time, not as a list.
- For additional shared principles (scope awareness, handling disagreement), see `references/interactive-principles.md`.

## Output Contract — Progress Footer (mandatory)

Every assistant message in this skill **must end with a progress footer as the LAST line**. No exceptions while the interactive flow is active — this includes clarifying questions, short acknowledgements, and messages that contain only code. A message without this footer is a contract violation.

**Format:**
- Generic step: `Step 1/2 · Checkpoint 2/4 — Assumptions and Review Questions: gap follow-up`
- Findings walkthrough (CP3): `Step 2/4 · Checkpoint 3/4 — Findings: finding 2 — race condition`
- Without steps: `Checkpoint 1/4 — Change Intent and Entry Flow`

Rules:
- **During CP3 Findings Walkthrough, the `Step M/N` counter tracks findings.** N is the total finding count; M is the finding currently being discussed. The trailing descriptor is `finding M — <short title>`.
- **Discussion does not advance the counter.** The developer may interrupt during a finding walk to ask for code outlines, adjacent symbol explanations, or data-flow traces. The footer stays on the current finding until the developer explicitly advances. Return phrasing: *"Back to finding M — ready to advance, or more to discuss?"*

The footer is a single line, rendered verbatim, at the very bottom of the message — nothing after it.

**Exceptions:** Omit the footer only when the developer has explicitly opted out of the interactive flow — report-only invocation, non-interactive subagent mode, trivial-diff fast path, or an explicit "give me the full report" request.

## Scope Awareness

- For large diffs (30+ files or 1000+ lines): batch the review by feature area rather than attempting equal depth on everything. The chained `/diff-review` walk is the place where per-file/per-hunk prioritization happens — its CP2 walk order already starts at the biggest logical change and pulls hot-risk areas (auth / data mutation / shared libraries / interceptors) forward as a tiebreaker.
- If the diff is too large to fit in context, state this explicitly and propose reviewing in batches.

### Trivial-Diff Fast Path

For trivial diffs (typo, formatting, dependency bump, single-line fix):

- Create and name the review artifact (required for tracking, same naming convention).
- Run gate checks but abbreviate to essentials (lint, compile; skip full test suite if the change is purely cosmetic).
- Present findings directly without the checkpoint walkthrough.
- Verdict and artifact path are still returned.

### Small-Diff Compact Path

For small diffs (under 15 files, single execution path, no cross-cutting concerns) that are not trivial — e.g., a focused bug fix, a single-feature addition within one concern:

- Create and name the review artifact.
- Run gate checks.
- Abbreviate to: CP1 (Change Intent), findings with severity and evidence, and verdict. Skip CP2 (assumptions stack) — it adds walkthrough overhead without proportional value for a focused change.
- Findings still get severity labels, file references, and evidence — the walkthrough structure is what gets compressed, not finding quality.
- If the small diff turns out to touch cross-cutting concerns (shared middleware, base classes, multi-tenant scoping), upgrade to the full checkpoint flow and announce: "Upgrading to full review: [reason]."

## Parallel Discovery (optional)

For shared protocol mechanics (complexity gate, spawn protocol, synthesis, on-demand triggers), see `references/parallel-agents.md`. For this skill's agent roster, return format schemas, and critique agent protocol, see `references/parallel-discovery.md`.

**Gate checks parallelism (all reviews):** Always run gate checks (lint, compile, test suite) in parallel with diff reading and execution-flow reconstruction — they are independent. Run gate checks as parallel Bash tool calls in a single message, not as sub-agents. No complexity gate needed for this; it applies to every review.

**Gate check fallback:** If gate checks cannot execute (no local environment, missing dependencies, subagent context), document which checks were attempted, why they failed, and whether CI results are available as a substitute. Report the gap in the gate check results table rather than silently skipping.

**Activation:** Medium+ tasks or diffs touching 15+ files spawn upfront agents automatically. For the 10-14 file range, medium+ classification on the layer criterion is sufficient — spawn. Override with `--parallel` or `--no-parallel`.

**Upfront agent roster (medium+ tasks):**
- **Execution flow tracer** — reconstruct current and changed execution flow from the diff entrypoints
- **Impact and dependency mapper** — map changed files to downstream consumers, shared interfaces, integration points
- **Risk checker** — check for in-flight changes on other branches, concurrent modification risk, dependency concerns

**Large diff batching (30+ files):** Spawn additional per-feature-area agents. Each agent covers one feature area and returns findings in the standard return format. The synthesis step merges feature-area findings into the unified review context.

**Phase placement:** Agents run during workflow steps 3-6 (execution flow reconstruction, change map, code walkthrough, per-file review plan). Synthesis feeds Checkpoint 1 framing and the Checkpoint 2 assumptions stack — it does NOT replace the chained `/diff-review` walk when one happened. Standalone `/review` (chain skipped) leans more heavily on agent synthesis to substitute for the missing walkthrough grounding.

**Critique agent:** Fires after workflow step 9 (Architecture, API, Framework, and Simplicity Gates), before Checkpoint 3 (Findings Walkthrough). Announce: "Spawning critique agent to review findings before walkthrough." Receives the diff and existing findings list. Returns: missed findings, contradictions, blind spots. New findings are added to the findings table as `pending` before CP3 walks them.

**Read `references/parallel-discovery.md` before spawning** — it contains the return format schemas required for each agent's spawn payload.

## Framework Adaptivity

- Works on any framework or stack. When framework context is known, reference concrete constructs and local conventions. When unclear, state that explicitly and mark related conclusions as conditional.

## Required Deliverables

- Every review produces two outputs: one persisted markdown report and one guided chat walkthrough. Run both by default. Skip the chat walkthrough only when the user explicitly asks for report-only output.
- Write to `.claude/docs/reviews` (create with `mkdir -p` if needed). Name: `NNN-<review-name>-YYYYMMDD.md` where `NNN` is the next zero-padded 3-digit prefix and `<review-name>` comes from the review title, branch, PR, or issue context (fallback: `review`).
- If the write fails or `NNN` cannot be computed (e.g., directory listing unavailable), use `001` as default and deliver the report inline.
- Keep revising that same file for the lifetime of the review.
- Update the file only when the findings set changes:
  - a new finding, question, or praise item is added
  - an existing finding changes severity, status, or recommended action
  - a previously open finding is resolved or dropped
- **Finding status column carve-out.** The findings table has a `Status` column with values `pending | walked | accepted-risk | dismissed | blocker-open`. This column is written live on every status transition — it is the single exception to the findings-change-only update rule. Everything else in the artifact still follows findings-change-only: evidence-only discussion that leaves the findings set unchanged does not trigger a rewrite.
- **Status semantics.** `pending` = not yet walked. Every other status is **terminal** — a finding in a terminal status is not re-walked in the same session unless the developer explicitly reopens it.
  - `walked` — the developer walked through the finding and acknowledged it. No further action required from the review. For a blocker the developer will fix *now* (in the same session or an immediately-following commit), use `walked` plus a rationale note naming the planned fix.
  - `accepted-risk` — design trade-off the developer explicitly accepts. Requires a rationale note.
  - `dismissed` — the developer rejected the finding. Requires a reason.
  - `blocker-open` — the developer agrees this blocks merge and it will NOT be fixed in the current session. Gates the verdict until a later session transitions it out of `blocker-open`.
- **Pre-verdict gate.** CP4 cannot issue a "ready to merge" verdict while any finding is `pending` or `blocker-open`. `walked`, `accepted-risk`, and `dismissed` do not gate the verdict.
- **Resume protocol.** Before walking any finding in CP3, read the findings table. Only walk findings with status `pending`. This is the single source of truth for where the session left off after interruption or across sessions.
- Return the saved file path in the final response.

## Guided Session Contract

- Do not lead with the full findings list or final verdict. Reveal findings only after walkthrough checkpoints have established the code path and review frame.
- Initial response must contain only: gate check results (pass/fail table), saved artifact path, code areas inspected, and first checkpoint content.
- Present the review in four checkpoints: change intent → assumptions/questions → findings walkthrough → tests/verdict. Comprehension of the change is delegated to `/diff-review` (chain in CP1) — `/review` does not walk the code itself.
- Start each checkpoint with `Checkpoint X/4: <title>`.
- Split dense checkpoints into steps when useful.
- Pause after each step and ask whether to continue or discuss.
- Do not auto-advance without confirmation.
- Ask 1-2 targeted reasoning questions per step that sharpen the developer's understanding of architecture fit and behavior.
- Keep questions concise and code-specific. Never generate random quiz questions — only surface challenges where actual gaps appear in the developer's thinking.
- When the developer's response reveals a gap in understanding, pause to fill it before continuing. Never skip over confusion to maintain checkpoint pace.
- Keep the findings walkthrough in chat; do not create a second markdown artifact for it.
- By the end of the session the developer should be able to explain, in their own words:
  - which assumptions the implementation depends on (CP2 output)
  - where the real risk sits (CP3 + CP4 synthesis)
  - which findings they accepted, dismissed, or marked as blockers (CP3 outcomes)
- "What changed", "how it aligns with architecture", and "what adjacent code controls behavior" are owned by the chained `/diff-review` walk — verify the developer can articulate them at CP1 before advancing; if not, prompt for the chain.
- End the findings walk by asking whether to continue into optional deep dives.

## Severity Scale

Every finding uses one of these severities:

- **blocker**: fails tests, breaks compilation, security hole, data corruption risk. Must be fixed before merge.
- **major**: architectural violation, missing test coverage for a critical path, regression risk. Should be fixed before merge unless explicitly accepted.
- **minor**: style inconsistency, performance micro-optimization opportunity, naming improvement. Fix or defer at developer discretion.
- **praise**: noteworthy strength worth calling out for reinforcement or team visibility.

## Default Thoroughness and Comment Selection

- Review deeply, then emit only high-signal output. Prefer fewer strong findings over many weak ones. Build every comment from concrete evidence, not style preference or generic advice.
- Each finding must include a file reference, severity, and when relevant, a practical change direction.
- Use `praise` for meaningful implementation strengths, `question` for unclear assumptions or intent.
- For files without comments, state briefly why none were needed. For architecture analysis, report only the highest-impact strengths or violations.

## Suggested Guided Checkpoints

### Checkpoint 1/4: Change Intent and Entry Flow

- Restate what changed, why it appears to exist, and what boundaries it touches.
- Identify the runtime entrypoint and name the first important review question, preferably about flow or architectural fit.
- **Chain hint to `/diff-review` (strong default).** `/diff-review` owns orientation and code comprehension — its HTML overview plus per-hunk walkthrough is the proper map of the change. `/review` does NOT walk the code itself; it depends on a prior `/diff-review` (or the developer's own reading) for grounding. Ask whether the developer wants to run `/diff-review` first; **default when the developer is ambiguous or says "you decide": chain to `/diff-review` first.** Skip the chain only when the developer explicitly declines (e.g., they wrote the change themselves and have the shape memorized) — when they do, surface the trade-off explicitly: *"Skipping the chain forfeits the walked grounding — findings will rest on agent synthesis (Execution flow tracer) plus my reading of the diff. Proceed?"*

### Checkpoint 2/4: Assumptions and Review Questions

- Turn the prior `/diff-review` walk (or, when standalone, agent synthesis + the diff reading) into a short stack of assumptions, invariants, and unresolved questions.
- Make clear which questions could flip the review outcome.
- Inclusion rubric: include assumptions that, if violated, would cause the change to fail in production or contradict the stated intent. Exclude assumptions obvious from the code (e.g., "the file exists" when the code just created it).

### Checkpoint 3/4: Findings Walkthrough

This is the core of `/review`. Each finding is walked one at a time. The developer advances only after resolving the current finding's status.

**Resume protocol (mandatory).** Before walking any finding, read the findings table in the persisted artifact. Walk only findings with status `pending`. Ignore `walked`, `accepted-risk`, `dismissed`, and `blocker-open` (the last is surfaced separately at CP4 as a gate). This is the single source of truth for where the session left off.

**Walk order.** Sort `pending` findings by severity: `blocker` → `major` → `minor` → `praise`. Within the same severity, order by file path for determinism.

**For each finding, in its own message:**

1. **Finding statement** — one sentence naming what is wrong and where. Severity emoji prefix required: 🛑 blocker · ⚠️ major · ℹ️ minor · ⭐ praise.
2. **Evidence excerpt** — the relevant code as a fenced block with `lang path:start-end` info string. If the finding spans multiple files, include the primary location's excerpt and optionally a short supporting excerpt from the contributing file. Keep each excerpt trimmed to the smallest self-contained block.
3. **Reasoning chain** — why the code path produces the risk. Two to four sentences. The developer should be able to restate this in their own words after the walk.
4. **Prompt for status transition** — ask the developer to decide one of:
   - **Acknowledge** → `walked` (terminal). The developer agrees with the finding and either will address it in the current session / immediate follow-up commit, or considers the observation fully captured. For a blocker-severity finding the developer commits to fix *now*, include a rationale note naming the planned fix.
   - **Accept as risk** → `accepted-risk` (terminal). Design trade-off the developer explicitly accepts. Requires a rationale.
   - **Dismiss** → `dismissed` (terminal). The developer rejects the finding. Requires a reason.
   - **Mark as open blocker** → `blocker-open` (terminal for this session; gates verdict). The finding blocks merge and will not be fixed in this session — resolution requires a later review pass.

   Write the transition to the findings table immediately. All four outcomes are terminal in the current session; only `blocker-open` (and any still-`pending` findings) will gate the CP4 verdict.

**Interactive exploration rule.** While a finding is being discussed, the developer may ask for code outlines, cross-references to other symbols, explanations of adjacent code, or data-flow traces. Exploration does **not** advance the finding counter — the footer stays on the current finding. Return phrasing after exploration ends: *"Back to finding M — ready to decide its status, or more to discuss?"*

**One finding per message.** Never batch findings. Keep open questions separate from confirmed findings — a question is not a finding and goes into CP2 or the artifact's Open Questions section.

**Cross-cutting findings carve-out.** A CP3 walk may reveal a finding that genuinely spans the whole change (e.g., "the combined diff introduces an invariant violation no single file owns"). This is the only class of findings that may be **added** during CP3 rather than pre-populated at the start of the walk. Insert it into the findings table with status `pending` and walk it **immediately after the current finding resolves**, even if its severity would otherwise place it later in the severity-sorted order. This is a permitted exception to the severity-sort rule — surface-while-fresh beats strict ordering for newly-discovered findings.

### Checkpoint 4/4: Tests, QA, Compatibility, and Verdict

- Walk the verification surface and missing test coverage.
- Present one major compatibility or resilience concern at a time when needed.
- **Manual QA checklist**: Present concrete, route-based user-facing checks that must be exercised before the change can be accepted. Organize by affected route or user entrypoint. Each check should be a specific action with an expected outcome (e.g., "Navigate to /inbox → click Mark All Read → verify badge clears and toast appears"). Skip this if the change is purely internal with no user-facing impact.
- **Synthesis check**: Before the verdict, ask the developer to articulate the real risk and where it sits — without referring to the diff. If they can explain the risk chain in their own words, the review succeeded. Fill any remaining gaps.
- **Pre-verdict gate (mandatory).** Read the findings table. If any finding is `pending` or `blocker-open`, the skill CANNOT issue a "ready to merge" verdict. State which findings gate the verdict and return to CP3 to resolve them, or halt the session with a clear "not merge-ready — N findings open" summary. `walked`, `accepted-risk`, and `dismissed` are all terminal and do not gate.
- State the merge-readiness verdict.
- Summarize strengths, blockers, and optional deeper areas to inspect next. List every `accepted-risk` finding in the final summary with its rationale for future refactoring visibility.
