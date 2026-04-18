# Scout — Parallel Discovery Details

Skill-specific agent roster, return format schemas, and phase details for the scout skill's parallel discovery mode. For shared protocol mechanics (complexity gate, spawn protocol, synthesis, on-demand triggers, visibility), see `parallel-agents.md` (sibling in this directory).

## Upfront Agent Roster

### Code-Path Tracer

Trace the entrypoint, map execution flow, identify adjacent modules and boundary crossings. For bug scouts, focus on the root-cause execution path rather than the usage trace.

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

### Impact Mapper

Find all files in the affected area, check test coverage status, map ripple impact.

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

### In-Flight Change Checker

Check other branches for concurrent modifications to the same files. Focus on branch conflicts and merge risk — general risk analysis belongs to the Impact Mapper.

```
## In-Flight Branch Conflicts
- [branch] touches [files] — [merge risk assessment]

## Dependency Concerns
- [dependency] — [concern]

## Additional Notes
[free text]
```

## Phase Placement

Agents run before Checkpoint 1. Synthesis feeds CP1 (Problem Frame) and CP2 (Code Walkthrough & Questions). Checkpoints present and discuss synthesized findings rather than exploring inline.

## Critique Agent

None. Scout's interactive checkpoints surface gaps naturally through developer questions. The general on-demand protocol handles mid-checkpoint research needs.
