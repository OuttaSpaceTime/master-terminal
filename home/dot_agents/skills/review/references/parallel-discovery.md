# Review — Parallel Discovery Details

Skill-specific agent roster, return format schemas, critique agent protocol, and phase details for the review skill's parallel discovery mode. For shared protocol mechanics (complexity gate, spawn protocol, synthesis, on-demand triggers, visibility), see `parallel-agents.md` (sibling in this directory).

## Gate Checks Parallelism

Always run gate checks (lint, compile, test suite) in parallel with diff reading and execution-flow reconstruction — they are independent. Run gate checks as parallel Bash tool calls in a single message, not as sub-agents. No complexity gate needed for this; it applies to every review regardless of size.

## Upfront Agent Roster

### Execution Flow Tracer

Reconstruct current and changed execution flow from the diff entrypoints.

```
## Execution Flow (Current)
1. [step] — path:line
...

## Execution Flow (Changed)
1. [step] — path:line
...
(max 15 steps each)

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

### Impact and Dependency Mapper

Map changed files to downstream consumers, shared interfaces, integration points.

```
## Affected Files
| File | Current Responsibility | Why Impacted | Risk |
|---|---|---|---|
| path | [role] | [reason] | low/med/high |

## Test Coverage
- [file/area]: [covered / partially covered / no coverage] — [test file if exists]

## Ripple Impact
- [module] → [downstream effect]

## Additional Notes
[free text]
```

### Risk Checker

Check for in-flight changes on other branches, concurrent modification risk, dependency concerns.

```
## Risk Flags
| Risk | Scenario | Likelihood | Blast Radius |
|---|---|---|---|
| [name] | [concrete sequence of events → bad outcome] | low/med/high | [scope] |

## In-Flight Branch Conflicts
- [branch] touches [files] — [merge risk assessment]

## Dependency Concerns
- [dependency] — [concern]

## Additional Notes
[free text]
```

## Large Diff Batching (30+ files)

Spawn additional per-feature-area agents. Each agent covers one feature area and returns findings using the most appropriate schema from this file. The synthesis step merges feature-area findings into the unified review context.

## Phase Placement

Agents run during workflow steps 3-6 (execution flow reconstruction, change map, code walkthrough, per-file review plan). Synthesis feeds Checkpoint 1+ walkthrough.

## Critique Agent

Fires after workflow step 9 (Architecture, API, Framework, and Simplicity Gates), before Checkpoint 5 (Findings Walkthrough).

### What the critique agent receives

The critique agent starts cold like any other agent. Its spawn prompt must include:

1. **The diff** — the full diff output (`git diff main...HEAD` or equivalent)
2. **The existing findings list** — the findings table from the review artifact so far, with all columns
3. **Scope boundaries** — stated review scope and acceptance criteria
4. **The critique mandate** — "Review this diff and findings for: missed findings, contradictions, blind spots, undertested paths. Use the return format below. Max 1000 words."
5. **Constraints** — "Do not implement changes. Critique only. Stay within the return format."

### Return format

```
## Missed Findings
- [finding] — severity: [blocker/major/minor] — [evidence at path:line]

## Contradictions
- [finding A] vs [observed code] — [which is correct and why]

## Blind Spots
- [area not covered] — [why it matters for this diff]

## Untested Paths
- [path] — [what could break]

## Additional Notes
[free text]
```

### How findings merge

- Critique agent findings are reviewed by the main thread before merging.
- Valid findings are added to the findings table as `pending` before CP5 walks them.
- Invalid or low-value findings are discarded — the critique agent is advisory, not authoritative.
