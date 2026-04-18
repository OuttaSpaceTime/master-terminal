# Plan — Parallel Discovery Details

Skill-specific agent roster, return format schemas, critique agent protocol, and phase details for the plan skill's parallel discovery mode. For shared protocol mechanics (complexity gate, spawn protocol, synthesis, on-demand triggers, visibility), see `parallel-agents.md` (sibling in this directory).

## Upfront Agent Roster

Upfront agents spawn only in Mode B (no scout). Mode A inherits the scout's discovery and skips upfront agents by default. Exception: if the inherited scout is stale or the plan needs to validate specific claims against current code, upfront agents may spawn on a case-by-case basis with an announced reason.

### Entrypoint Flow Tracer

Trace trigger-to-outcome execution path, map architectural boundaries.

```
## Execution Flow
1. [step] — path:line
2. [step] — path:line
...
(max 15 steps)

## Entry/Exit Points
- Entry: [description] — path:line
- Exit: [description] — path:line

## Branch Decisions
- [condition] at path:line → [outcome A] / [outcome B]

## Adjacent Modules
- [module] — path — [why it matters]

## Additional Notes
[free text for anything that doesn't fit the schema above]
```

### Pattern Reference Reader

Read the most similar existing feature for conventions, naming, structure, test style.

```
## Conventions Observed
- Naming: [pattern]
- File structure: [pattern]
- Import style: [pattern]

## Test Style
- Framework: [name]
- Pattern: [description]
- Helpers: [existing utilities]

## Most Similar Feature
- [feature name] at [path] — [why it's the best pattern reference]

## Additional Notes
[free text]
```

### Test Infrastructure Scanner

Check test helpers, patterns, existing coverage, framework-specific test utilities.

```
## Test Framework
- [framework] — [config location]

## Existing Helpers
- [helper] at [path] — [what it does]

## Coverage Gaps
- [area] — [what's missing]

## Patterns
- [test type]: [how it's done in this codebase, with example path]

## Additional Notes
[free text]
```

## Phase Placement

Agents run during Steps 1-5 (discovery phase). Synthesis feeds Step 6+ (planning phase). If the project has a verification suite, run gate checks in parallel with upfront agents.

## Critique Agent

Fires after Step 13 (Draft Diffs), before Step 14 (Readiness and Finish Signals).

### What the critique agent receives

The critique agent starts cold like any other agent. Its spawn prompt must include:

1. **The complete plan artifact** — the in-memory plan text including all sections through Step 13 (draft diffs or explanation if withheld). Paste the full artifact into the prompt.
2. **Scope boundaries** — the stated Now/Later/Out boundaries
3. **The critique mandate** — "Review this plan for: missed implementation steps, ordering bugs, untested paths, scope creep beyond guardrails, and contradictions. Use the return format below. Max 1000 words."
4. **Constraints** — "Do not implement changes. Critique only. Stay within the return format."

### Return format

```
## Missed Items
- [item] — [why it matters]

## Ordering Concerns
- [step] should come [before/after] [other step] — [why]

## Untested Paths
- [path] — [what could break]

## Scope Concerns
- [item] — [how it exceeds stated boundaries]

## Contradictions
- [claim A] vs [claim B] — [which is correct and why]

## Additional Notes
[free text]
```

### How findings merge

- Critique agent findings are reviewed by the main thread before merging.
- Valid findings are added to Step 14 (Readiness and Finish Signals).
- Invalid or low-value findings are discarded — the critique agent is advisory, not authoritative.
