---
name: control-flow-trace
description: Trace end-to-end control flow for bugs, unexpected behavior, or execution flow understanding. Produces gap-free, line-referenced execution walkthroughs with type constraints, value propagation, architectural context, and root-cause diagnosis. Traces through application code and dependency/framework internals (including node_modules). Use when investigating race conditions, state inconsistencies, unexpected request patterns (e.g., duplicate calls), stale data bugs, missing/wrong values propagating across layers, or when asking "what exactly happens when X?" and needing a precise line-by-line answer. NOT for architecture reviews or optimization discussions.
---

# Control Flow Trace

## Goal

Given a symptom (bug, unexpected behavior, or execution question), produce a deterministic, gap-free, line-referenced walkthrough from entry point to observed outcome. Make three things explicit: (1) the architectural boundary where the issue lives, (2) the root cause, and (3) evidence that the trace is complete. Cross into dependency internals when the causal chain requires it — including framework code in `node_modules`.

## Interactive Constraints (mandatory)
- ONE concept per message, under 200 words of prose. Pause after each step or checkpoint.
- 3-12 lines of prose per message. If more is needed, split.
- Code snippets: use fenced blocks with `lang path:start-end` info string and enclosing context.
- If developer says "skip" or "I know this," fast-forward immediately.
- For additional shared principles (scope awareness, handling disagreement), see `references/interactive-principles.md`.

## When to Use

Use this skill when investigating:
- Race conditions or timing-dependent bugs
- State inconsistencies (value is X in one place, Y in another)
- Unexpected request patterns (duplicate calls, missing calls, wrong order)
- Stale or missing data propagating across layers
- Wrong branch taken due to unexpected input shape or type
- **Execution flow understanding** — "What exactly happens when a user does X?" Trace the full path with line references.

## When NOT to Use

- **Architecture reviews** — "Is this the right pattern for X?" Use explore-solutions or a design discussion.
- **Optimization** — "Why is this slow?" Use profiling tools; a control-flow trace shows *what* executes, not *how long*.

## Output Structure

Render the final answer in markdown with these sections in order:

1. `## 1) High-level overview` — brief summary
2. `## 2) Step-by-step control-flow trace` — main body; each step uses required fields below
3. `## 3) Architectural context` — boundaries, invariant ownership
4. `## 4) Concise diagnosis` — primary root cause
5. `## 5) Trace completeness and finish signals` — proof of end-to-end coverage
6. `## 6) Potential solutions` — only when requested or when confidence is high

The trace must be gap-free: never jump from one layer, function, or state transition to another without showing the bridging step.

Inside section 2, render each step as:

- `### Step N: <short action title>`
- Start with `**Control-flow explanation:**` so the reader gets the mental model first.
- Put source location inside each signature heading instead of separate `Code location` and `Code path` lines.
- Use short lines; split long data across multiple lines instead of one wrapped paragraph.

At the top of section 2, add a compact trace map:

- `#### Trace map`
- A markdown table with columns: `Step`, `Code location`, `Transition`.

Use fenced code blocks for these repeated step artifacts:

- `Affected function declaration (with arguments)` as a language-appropriate code block.
- `Signature outline (focused path)` as a language-appropriate code block.

Do not output step content as a single dense bullet paragraph.

If the user asked only for explanation, omit section 6.
If root-cause confidence is low, replace section 6 with `Open questions blocking safe fixes`.

## Step Requirements

### Granularity

A step is one logical handoff point: when control leaves one function/component/layer and enters another, or when state/input fundamentally changes type or meaning. Do not create a step for each line of code within a single function unless a meaningful transformation or branch occurs.

### Structure

For each step, include all of these fields:

- `Control-flow explanation` — what this step does and why
- `Type requirements / checking / constraints` — relevant type signatures, guards, or narrowing
- `Example input` — concrete values entering this step (propagated from previous step's output)
- `Affected function declarations (with arguments)` — fenced code block of the declaration
- `Signature outlines (focused path)` — fenced code block showing only the relevant path; use `...` for unrelated code
- `How this wires into next step` — the exact value, call, event, or branch result that becomes the next step's input

Each signature heading must identify the active class or module and include file path plus a 1-based line number or line range.
`Affected function declarations` must include argument names with types and defaults when present in source.

### Content

- Include concrete values that move forward across steps.
- Propagate previous output into the next step's `Example input`.
- Include branch conditions and evaluated boolean results.
- Show the exact parameter map/query/body if request behavior is involved.
- Distinguish expected vs actual values when diagnosing a bug.
- If a value is unknown, label it `Assumed example`.
- Only include the signatures needed for that step; do not dump unrelated declarations.

### Authoring Discipline

- Keep one causal action per step.
- Lead with what the step does before listing evidence.
- Do not skip intermediate hops. If Step N produces a value and Step N+1 consumes it elsewhere, include every meaningful handoff in between.

## Tracing Through Dependency Internals

When a bug crosses the boundary between application code and a dependency (npm package, gem, pip package, Go module, etc.):

### Locating Dependency Source

Provide ecosystem-appropriate commands for opening dependency source:

- **Node.js/npm**: `node -e "console.log(require.resolve('<package>/path/to/file'))"`
- **Ruby/gems**: `bundle open '<gem>' --path '<file>'`
- **Python/pip**: `python -c "import <package>; print(<package>.__file__)"`
- **Go**: Source is in the module cache at the path shown by `go env GOMODCACHE`

### Framework Internals

When the trace crosses into a framework (Angular, Express, Rails, etc.):

- **Always read the actual source** in `node_modules` (or equivalent). Do not assert framework behavior from memory — verify it. Use the ecosystem-appropriate commands above to locate the file.
- Show the exact file, method signature, and relevant code path inside the framework.
- Keep framework steps concise: show the handoff logic, not the full implementation. The goal is to prove the causal chain is unbroken, not to document the framework.
- State the framework version (from `package.json` or lock file) since behavior may differ across versions.

### Trace Termination

A trace ends when one of these is reached:
- **The observed symptom** — the bug or behavior the user asked about is fully explained.
- **A system boundary exit** — browser navigation (`window.location`), process exit, network response sent. State what happens after the boundary but do not trace past it.
- **An external system** — database write, third-party API call, message queue publish. State what was sent and stop.

If the user asked "what happens when X" (explanation, not bug), the trace ends when the terminal observable outcome is reached and all side effects are accounted for.

### Tracing Strategy

Choose instrumentation by where the bug manifests, then escalate as needed:

| Bug location | Approach |
|---|---|
| Test-triggered | Instrument in the test; prefer stack traces or breakpoints first |
| Application runtime | Instrument at the application boundary; gate by env var |
| Unreachable code path | Dedicated debug script with minimal instrumentation |

**Escalation order** (simplest first): stack trace > logged exception backtrace > debugger breakpoint > runtime instrumentation (e.g., `TracePoint`, `--inspect`, `sys.settrace`)

### Dependency Walkthrough Requirements

For each step that enters a dependency:

- State which dependency and version
- Provide the command to open the dependency source
- Show the exact file and method signature
- Include enough code context to show the handoff to the next step
- Explain why this matters for the observed bug
- State what flows into the next step

## Section Field Requirements

**Section 3 — Architectural context** must include:
- `Boundaries touched`
- `Invariant owner`
- `Stable responsibilities`
- `Change pressure` — what would move only if a deeper redesign is needed

**Section 5 — Trace completeness** must include:
- `Entry point`
- `Observed symptom / terminal state`
- `Proof the trace is complete (full causal chain covered)`
- `Gaps that would keep the analysis incomplete`

**Section 6 — Potential solutions** (only when user asked for fixes or root cause is high-confidence):
- `Option A (minimal)` with exact file targets
- `Option B (hardening)` with guards or defensive checks
- `Why this boundary` — architectural reason the fix belongs there
- `Risk/impact` notes
- `Recommended option`
- When multiple contributing factors exist, state primary root cause and list secondary factors separately.

## Workflow

### Scoping

- If the full trace would exceed ~30 steps, group consecutive steps within the same module/function into a single summarized step, noting the grouped range.
- Always keep boundary-crossing steps (between modules, services, or layers) as individual steps.
- For very complex systems, state the scoping decision explicitly before beginning the trace.

### Steps

1. Identify symptom and boundary:
   - Entry trigger (route, event, subscription, lifecycle hook, API handler).
   - Observed wrong behavior (duplicate call, stale state, wrong branch).
   - State what starts the trace and what observable result is expected to complete it.

2. Collect minimal code path:
   - Search for emitters, handlers, service methods, transport layer, and rendering side effects.
   - Capture line-number references for each transition.
   - Read adjacent unchanged code when it defines the invariant, extension point, or ownership boundary.

3. Build typed flow chain:
   - For each hop, state expected input/output types.
   - Add concrete runtime examples that pass through each hop.
   - Insert a new step whenever the explanation would otherwise need "then it gets used" without showing where that handoff actually occurs.

4. Build the architecture model:
   - Name the boundaries touched by this flow: controller, service, model, worker, client, store, persistence layer, external API, or equivalent.
   - State which component owns the invariant that fails or holds.
   - State which responsibilities stay stable and which would need to move if a fix changes design.

5. Isolate divergence point:
   - Mark first step where actual value violates expected invariant.
   - Explain why this creates the observed symptom.

6. Complete the trace:
   - State the end-to-end outcome that proves the trace is complete.
   - State what evidence would still keep the analysis incomplete.

7. Propose fixes only when warranted:
   - If the user asked for fixes or the root cause is clear, add at least one minimal fix and one hardening fix.
   - Include tradeoffs, blast radius, and why the fix belongs at that boundary.

## Worked Example

**Symptom:** "Why does `POST /api/v2/tasks` fire twice when the user clicks 'Create' once?"

### 1) High-level overview

The button click triggers a form submission that calls `TaskService.create()`. The component subscribes to the returned Observable twice: once in the template via `async` pipe and once imperatively in the click handler. Each subscription initiates an independent HTTP request.

### 2) Step-by-step control-flow trace

#### Trace map

| Step | Code location | Transition |
|------|---------------|------------|
| 1 | `create-task.component.html:12` | Button `(click)` emits to handler |
| 2 | `create-task.component.ts:45` | Handler calls `TaskService.create()` |
| 3 | `task.service.ts:31` | Returns cold `Observable<Task>` via `HttpClient.post()` |
| 4 | `create-task.component.ts:47` | Handler `.subscribe()` — first subscription, first HTTP request |
| 5 | `create-task.component.html:18` | Template `\| async` — second subscription, second HTTP request |

#### Step 1: Button click event

**Control-flow explanation:** User clicks "Create". Angular event binding invokes the component method.

**Type requirements:** `(click)` binding expects `($event: MouseEvent) => void`

**Example input:** `MouseEvent { target: <button> }`

**Affected function declaration:**

```html
<!-- create-task.component.html:12 -->
<button (click)="onSubmit()">Create</button>
```

**How this wires into next step:** Angular calls `CreateTaskComponent.onSubmit()`.

#### Step 2: Handler calls service

**Control-flow explanation:** `onSubmit()` reads form values and delegates to the service.

**Example input:** `{ title: 'Fix login bug', assigneeId: '42' }`

**Affected function declaration:**

```typescript
// create-task.component.ts:45 — CreateTaskComponent
onSubmit(): void {
  this.task$ = this.taskService.create(this.form.value);
  this.task$.subscribe(task => this.router.navigate(['/tasks', task.id]));
}
```

**How this wires into next step:** `this.taskService.create()` returns a cold Observable, assigned to `this.task$`.

#### Step 3: Service returns cold Observable

**Control-flow explanation:** `create()` returns `HttpClient.post()`, which is cold — each `.subscribe()` triggers a new HTTP request.

**Type requirements:** `create(attrs: TaskAttributes): Observable<Task>`

**Example input:** `{ title: 'Fix login bug', assigneeId: '42' }`

**Affected function declaration:**

```typescript
// task.service.ts:31 — TaskService
create(attrs: TaskAttributes): Observable<Task> {
  return this.http.post<Task>('/api/v2/tasks', { data: { attributes: attrs } });
}
```

**How this wires into next step:** The returned Observable is subscribed to in two places.

#### Step 4: First subscription (imperative) -- DIVERGENCE POINT

**Control-flow explanation:** The `.subscribe()` in `onSubmit()` triggers the first `POST` request.

**Example input:** Cold Observable from Step 3

**How this wires into next step:** `this.task$` is also bound in the template.

#### Step 5: Second subscription (template async pipe)

**Control-flow explanation:** The template uses `task$ | async`, which calls `.subscribe()` a second time, triggering a second identical `POST` request.

```html
<!-- create-task.component.html:18 -->
<div *ngIf="task$ | async as task">Created: {{ task.title }}</div>
```

### 3) Architectural context

- **Boundaries touched:** Component template, component class, HTTP service
- **Invariant owner:** Component — it decides how many times to subscribe
- **Stable responsibilities:** `TaskService.create()` correctly returns a cold Observable (standard `HttpClient` behavior)
- **Change pressure:** None — the service API is fine; the fix is local to the component

### 4) Concise diagnosis

**Primary root cause:** The component subscribes to the same cold HTTP Observable twice — once imperatively in the handler and once via `| async` in the template. Each subscription independently executes the POST request.

### 5) Trace completeness and finish signals

- **Entry point:** `(click)` event on the Create button
- **Observed symptom:** Two `POST /api/v2/tasks` requests in the network tab
- **Proof the trace is complete:** Every subscription site is accounted for; two subscriptions on a cold Observable produce exactly two requests
- **Gaps:** None — the Observable has no other subscribers

### 6) Potential solutions

- **Option A (minimal):** Use `shareReplay(1)` on the Observable before assigning to `task$`, so both subscribers share a single execution.
- **Option B (hardening):** Remove the imperative `.subscribe()` entirely; use only the `| async` pipe and handle navigation via a `tap()` side effect in the Observable chain.
- **Why this boundary:** The component owns the subscription strategy; the service should remain stateless.
- **Risk/impact:** Option B is preferred — it eliminates manual subscription management and prevents future re-subscription bugs.
- **Recommended option:** Option B

## Quality Checklist

Before finalizing, verify each group:

**Steps**
- Every step has all required fields and a line-referenced path.
- Every signature heading identifies class/module + file path:line.
- Fenced code blocks used for declarations and signature outlines.
- Value flow is continuous — no step-to-step jump hides a transition, callback, query, or state change.

**Structure**
- Section and step heading hierarchy matches the output structure.
- Section 2 starts with a trace-map table.

**Sections**
- Architectural context names boundaries, invariant ownership, and stable responsibilities.
- Diagnosis points to one primary root cause.
- Trace completeness names proof that the end-to-end flow is covered.
- Solutions appear only when warranted and map to the root cause.
- Dependency steps include source-opening commands and version context.
