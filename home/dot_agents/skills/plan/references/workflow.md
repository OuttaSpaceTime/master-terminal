# Plan Skill — Output Template

Use this structure. Include conditional sections only when relevant — omit them entirely otherwise.

```markdown
# <Feature Name> - Implementation Plan

## Report Location
- Saved file: `.claude/docs/plans/plan-YYYYMMDD-HHMMSS.md`

## Planning Mode
- Mode: `<Scout-Backed Planning | Direct Planning With Minimal Discovery>`
- Source of understanding: `<scout path or discovery summary>`

## Discovery Assessment
_Required for Mode B. Omit for Mode A (scout already resolved ambiguities)._

| Ambiguity | Classification | Evidence |
| --- | --- | --- |
| <what was uncertain> | <resolved / isolated / broad> | <what discovery found, or why it remains> |

- **Path chosen**: <all resolved → proceed / isolated → options below / broad → recommend /scout>
- **Reasoning**: <why the ambiguity level warrants this path>

## TL;DR
- <core approach>
- <biggest risk>
- <main dependency or unknown>

## Source Requirements (Verbatim)
<issue/story/criteria copied exactly>

## Objective
- <business and technical objective>

## Scope Guardrails
- In scope: <item>
- Out of scope: <item>
- Assumptions: <item>
- **Known**: <fact established from code or scout — high confidence>
- **Inferred**: <working assumption, likely true but not fully confirmed>
- **Unknown**: <unresolved item that could change the plan>

## File Impact
| File or Area | Impact | Current Responsibility | Why Impacted | Planned Change | Risk | Confidence |
| --- | --- | --- | --- | --- | --- | --- |
| <path> | <create/modify/delete/reference> | <current role> | <reason> | <change intent> | <low/med/high> | <high/med/low> |

## Affected Tests / Checks
| Test or Check | What It Validates Today | Why Impacted | Planned Update | Risk | Confidence |
| --- | --- | --- | --- | --- | --- |
| <path or name> | <current validation> | <reason> | <update intent> | <low/med/high> | <high/med/low> |

## Before / After and Execution Flow
**Before:** <current behavior>

**After:** <planned behavior>

### Current Flow
1. <step>
2. <step>

### New Flow
1. <step>
2. <step>

### Deltas
- <what changes and why>

## Implementation Steps
1. <step> — Tested by: T1, T2
2. <step> — Tested by: T3

## Testing Strategy
| Requirement | Test Scenario (precondition → action → expected outcome) | Test Type (with rationale) | Pattern/File to Follow | Mocking Approach | New/Update | Verification Command |
| --- | --- | --- | --- | --- | --- | --- |
| <requirement> | <given X, when Y, then Z> | <unit/integration/e2e — why> | <existing spec path> | <what mocked, what real, which helpers> | <new/update> | `<command>` |

## Finish Signals
- Trigger: <what starts the flow>
- Behavior complete when: <specific observable state change>
- Verification complete when: <specific command that returns pass/fail>
- Still unfinished if: <known gap, failing check, unresolved blocker>

## Confidence Gate
| Check | Status | Evidence |
| --- | --- | --- |
| 1. Current execution flow traced end-to-end | <PASS/FAIL> | <one-line evidence> |
| 2. New execution flow traced end-to-end | <PASS/FAIL> | <one-line evidence> |
| 3. All impacted files read and validated | <PASS/FAIL> | <one-line evidence> |
| 4. Syntax and patterns match existing code | <PASS/FAIL> | <one-line evidence> |
| 5. API contract is known | <PASS/FAIL> | <one-line evidence> |
| 6. Test scenarios mapped with mocking strategy | <PASS/FAIL> | <one-line evidence> |

**Result**: <all passed → diffs included / N checks failed → diffs withheld>

## Draft Diffs (Not Applied)
### `<path/to/file.ext>`
<one-line purpose>

```diff
  context
- old line
+ new line
  context
```

If draft diffs are withheld:

## Draft Diffs (Withheld)
- <why confidence is not yet high enough>
- <what must be learned or resolved first>

## Open Questions / Blockers
- <unresolved item>

---
<!-- Conditional sections: include only when relevant, omit entirely otherwise -->

## Architectural Change Model
_Include only when introducing new abstractions, patterns, or architectural boundaries._
- <what stays intact>
- <what new responsibility or boundary is introduced>
- <what existing pattern the plan follows>

## Compatibility and Failure Risk
_Include only when modifying shared interfaces, data schemas, API contracts, or crossing architectural boundaries._
| Area | Status | Potential Breakage | Mitigation Direction |
| --- | --- | --- | --- |
| <area> | <compatible/conditional/breaking> | <risk> | <mitigation> |

## Potential Issues and Reproduction
_Include only when there are non-obvious failure modes worth documenting._
### Issue: <short name>
Why it can happen:
- <cause>

Reproduce:
1. <step>

## Implementation Constraints
_Include only when there are genuine DO NOT / MUST / STOP rules beyond standard project conventions._
| Constraint | Type | Rationale |
| --- | --- | --- |
| <constraint> | <Negative/Positive/Checkpoint> | <why> |
```
