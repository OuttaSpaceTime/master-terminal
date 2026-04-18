## Workflow

### 1. Gather Review Context

- Compare branch changes against mainline, then include staged or unstaged changes if needed.
- Prefer this sequence:
  1. `git --no-pager diff main...HEAD`
  2. use `master...HEAD` when `main` is absent
  3. fall back to `git --no-pager diff` when no branch diff exists
- Collect issue, ticket, or acceptance-criteria context.
- If acceptance criteria are missing, mark that as a review limitation.
- Pick the review title early so the numbered artifact can be named once and then updated in place.

### 2. Run Gate Checks

Run the project's full verification suite before code analysis. A failing test or compile error is a blocker finding regardless of what the code looks like on paper — always use the complete suite, not per-file targeting.

Discover what to run from `CLAUDE.md` / `.claude/rules/`, CI config (`.github/workflows/`, `.gitlab-ci.yml`), `package.json` scripts, or `Makefile`. Common patterns:

| Stack | Gate checks |
|---|---|
| Angular | `npx editorconfig-checker`, `npx ng lint`, `npx ng serve --port <free>` (background, wait for compile), `npx ng test --watch=false --browsers=ChromeHeadlessNoSandbox`, `node strict-migrate.mjs` if types touched |
| Node / TS | lint, `tsc --noEmit`, full test runner |
| Python | lint (`ruff`/`flake8`), `pytest`, type-check if configured |
| Go | `go vet ./...`, `go test ./...` |

Record results in the review artifact under a `## Gate Checks` table:

```
| Check       | Result               | Notes                            |
|-------------|----------------------|----------------------------------|
| lint        | ✅ pass              |                                  |
| compilation | ✅ compiled          |                                  |
| test suite  | ❌ 2 failures        | FooComponent, BarService         |
```

Any failure becomes the primary finding in Checkpoint 5.

### 3. Reconstruct the Actual Execution Flow Early

- Build the current and changed execution flow as one of the first analysis steps.
- Start from the real entrypoint touched by the diff and trace forward in runtime order.
- Record:
  - which branch or trigger starts the flow
  - which modules or services execute next
  - which conditions or guards redirect behavior
  - which side effects, contracts, or integrations are touched
  - where the flow ends, fails, retries, or rolls back
- Distinguish clearly between:
  - observed current flow
  - changed flow introduced by the diff
  - inferred flow segments that still need confirmation
- Use this execution-flow model as the backbone for the rest of the review.

### 4. Build a High-Level Change Map

- Create a file summary table: file path, artifact type, purpose, key change.
- Add a short summary of the change approach.
- Summarize the primary execution flow touched by the diff using the earlier runtime trace.
- Note dependencies, integration boundaries, and shared-code impact.
- Identify whether each changed file looks essential to the stated problem or whether the diff appears broader than necessary.
- Identify the existing architectural pattern and local style conventions the change is expected to follow.

### 5. Walk the Affected Code Before Findings

- Trace the relevant code path in execution order, anchored to the earlier execution-flow reconstruction.
- Include adjacent unaffected code when it explains lifecycle, invariants, or error handling.
- Record where behavior is explicit versus where assumptions are being made.
- Capture the key review questions raised by the walkthrough.

### 6. Build a Per-File Review Plan

- Create a short plan: `file -> risk level -> review focus`.
- Allocate the deepest review attention to high-risk areas such as auth, payments, data mutation, async orchestration, routing, and shared libraries.
- Reserve explicit testing scrutiny for each high-risk path.
- This plan feeds Checkpoint 3 (Critical Hot Spots) — which walks only the one or two highest-risk files, not every file. Exhaustive per-file code comprehension is `/diff-review`'s job; `/review` uses the per-file plan to pick hot spots and to inform which files the findings will reference.

### 7. Review for Correctness and Risk

Check and report:

- change minimality and scope discipline
- architecture and code-style alignment with the surrounding codebase
- locality of definition and avoidance of preemptive abstraction
- domain correctness and invariant safety
- acceptance-criteria coverage and missing behavior
- bug and regression risk
- error handling, edge cases, and async timing hazards
- performance and scalability risks
- security and privacy risks
- test coverage and missing scenarios
- manual QA checks that must be exercised before the change can be accepted, organized by affected route or user entrypoint
- code smells that materially harm maintenance

### 8. Run the Focused Bug and Smell Checklist

Explicitly check relevant items:

- subscription, listener, or resource leaks
- race conditions and ordering bugs
- undefined or null safety on accessed values
- failure propagation and error-handling completeness
- dead code and unused imports
- magic numbers or strings that hide intent
- nested conditionals that obscure logic risk
- oversized functions or templates that reduce testability

### 9. Run Architecture, API, Framework, and Simplicity Gates

- Judge architecture compliance against existing boundaries and patterns:
  - classify each major decision as `aligned`, `conditionally aligned`, or `violating`
  - cite concrete evidence with `path:line`
- Judge local code-style fit against nearby code in the same layer or feature:
  - naming, file structure, dependency direction, composition patterns, and testing style
  - report only deviations that materially hurt consistency, readability, or maintainability
- Judge diff scope and implementation minimality:
  - are all touched files and abstractions necessary for the stated change
  - does the implementation reuse existing helpers, patterns, and seams before introducing new ones
  - could the same behavior be achieved with a smaller or more local change
  - classify the scope as `minimal`, `acceptable but broad`, or `too broad`
- Judge abstraction locality:
  - is code defined close to where it is used when reuse is single-site or speculative
  - were helpers, utilities, hooks, services, or types extracted before a real second use or boundary existed
  - does the abstraction hide meaningful domain detail or make the code harder to follow in its primary usage path
  - classify each notable extraction as `locally justified`, `premature`, or `unclear`
- Judge API and abstraction quality when relevant:
  - is the public surface minimal and clear
  - are boundaries implementation-hiding
  - are seams testable without heavy setup
- Judge framework and library usage against:
  - existing repo conventions
  - best practices relevant to the touched APIs
- Judge solution complexity:
  - `minimal`
  - `acceptable complexity`
  - `overengineered`
- Convert non-trivial issues into actionable findings rather than optional commentary.

### 10. Review UI and UX Quality When the Diff Is User-Facing

Explicitly verify and report when relevant:

- reuse of existing UI patterns where appropriate
- manual testing evidence or missing evidence
- design-system or style-token alignment
- responsive behavior
- touch-device usability
- accessibility
- localization completeness
- route-based manual QA coverage required before acceptance, written as concrete user-facing checks

If UI changes are present, require screenshots or short videos for changed states.

### 11. Evaluate Compatibility, Resilience, and Production Safety

- Assess compatibility risks across:
  - data and schema behavior
  - API and public contract behavior
  - async jobs, notifications, events, or webhooks
  - external clients and integrations
- Classify each area as `compatible`, `conditional`, or `breaking`.
- Evaluate resilience where relevant:
  - timeout behavior
  - retry strategy and retry safety
  - idempotency
  - compensation or rollback boundaries
  - concurrency safety
- Evaluate operability where relevant:
  - logs, metrics, tracing
  - debuggability
  - rollout and rollback safety

### 12. Finalize Findings and Verdict

- Order findings by severity and user impact. In the interactive flow, this order drives the Checkpoint 5 walkthrough sequence: `blocker` → `major` → `minor` → `praise`, tie-broken by file path.
- Tie each finding to concrete evidence and a clear reasoning chain.
- **Findings status column.** Each finding carries a status: `pending | walked | accepted-risk | dismissed | blocker-open`. The status column is the single carve-out to the findings-change-only update rule — it is written live on every transition. `pending` means not yet walked; the other four are all terminal within the current session.
- **Walkthrough rhythm.** Findings are surfaced one per message in Checkpoint 5. Each message carries finding statement, severity prefix, evidence excerpt, reasoning chain, and a prompt for status transition. Interactive exploration during a finding walk does not advance the finding counter.
- State open questions separately from confirmed findings.
- Summarize notable strengths as well as problems.
- Make change-scope discipline explicit in the final summary, even when the conclusion is positive.
- Make abstraction-locality fit explicit in the final summary, even when the conclusion is positive.
- Make architecture fit and style fit explicit in the final summary, even when the conclusion is positive.
- **Pre-verdict gate.** The verdict cannot state "ready to merge" while any finding is `pending` or `blocker-open`. `walked`, `accepted-risk`, and `dismissed` do not gate. List the gating findings and return to Checkpoint 5, or halt with a "not merge-ready" summary.
- State the review verdict only after the walkthrough and question stack are complete and the pre-verdict gate passes.
- If manual QA is still required, make that explicit before signaling the change is acceptable.
- If the findings set changed, update the existing markdown artifact and append a revision note.
- If the findings set did not change, leave the artifact untouched and continue the discussion in chat (finding status transitions still write live per the carve-out).
- **Non-interactive / report-only mode.** When the skill is invoked non-interactively (subagent, report-only flag, or explicit "full report" request), compress all findings into a single findings-table section — the one-finding-per-message rhythm does not apply. The pre-verdict gate still applies: a report-only run cannot declare merge-ready while any finding is `pending` or `blocker-open`.

## Affected Code Walkthrough Requirements

- Walk the changed code and the important affected code before finalizing findings.
- Reconstruct the actual execution flow early, before broad judgment work.
- Trace in execution order where possible:
  - entrypoint
  - coordinator or container
  - domain or service logic
  - persistence or integration boundary
  - tests or missing test seams
- Include unchanged collaborators when they shape the reviewed behavior, data contract, lifecycle, or failure semantics.
- Separate:
  - observed behavior
  - inferred assumptions
  - unresolved review questions
- Prefer excerpts from changed symbols, but use adjacent symbols when they explain the real behavior better.

## Code Walkthrough Requirements

For each major checkpoint, include at least one `Code Walkthrough` block tied to concrete evidence.

Each `Code Walkthrough` block must include:

- symbol type: `class`, `function`, `method`, `template block`, or `module block`
- symbol name
- location: `path:line`
- code path: `path:line -> path:line -> ...`
- body excerpt trimmed to the relevant logic
- interpretation explaining what the code does
- review questions explaining what still needs to be checked before final judgment

Source constraints:

- Use excerpts only from the actual repository files under review.
- Do not invent pseudo-code.
- If trimming is necessary, keep exact code for included lines and replace omissions with short comments.
- Prefer exact excerpts over paraphrased code descriptions.

## Merge Request Comment Modeling

- Treat merge request comments as planned review outputs inside the single markdown artifact.
- Do not fetch existing MR threads, post platform comments, resolve threads, or synchronize with GitHub/GitLab APIs unless the user explicitly asks for a separate workflow.
- Maintain a planned comment inventory with statuses such as `new`, `unchanged`, `resolved`, and `dropped`.
- For each reviewed file, state either:
  - the planned MR comment(s) to leave
  - or why no comment is warranted and what is working well
- When discussion changes evidence but does not change the planned comment set or findings set, keep that update in chat only.
