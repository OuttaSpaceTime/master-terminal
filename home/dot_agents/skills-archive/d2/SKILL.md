---
name: d2
description: Trace code-level execution flows in a repository, produce D2 diagrams, render to SVG/PNG, and open from the terminal. This skill reads source code and diagrams the runtime path -- it is NOT for static architecture docs or high-level box diagrams drawn from memory. Use when a user asks to diagram, visualize, or map execution paths, guard chains, interceptor chains, request/response flows, branching logic, state machines, component interactions, or dependency graphs by tracing actual code.
---

# D2 Code Flow Diagrams

Trace a code path through the repo, write a D2 diagram, render it, and open for the user. Follow steps 1-4 in order.

## Required Input

The user must specify which flow to visualize. If the request is vague (e.g., "make a diagram"), ask what specific flow or interaction to render before proceeding.

Good requests: "visualize the dashboard access flow through guards", "diagram the HTTP interceptor chain".

## 1) Pick Flow

Match the scope of the user's request. When the request names a single function or guard, diagram just that. When it names a broader flow, prefer paths that cross multiple layers, for example:
- Router guards + resolver + redirect decisions.
- HTTP interceptor chain + error branches.
- Component -> service -> API -> state update -> navigation.

Use Grep/Glob to find the entry point, then Read each file along the path. Record every file path, function name, and branch condition you encounter -- these become diagram nodes and edges.

## 2) Trace Flow

### Common Entry Points

Start tracing from the function that initiates the flow:

| Flow type | Start at | Then follow |
|-----------|----------|-------------|
| Route guard / middleware | e.g., `canActivate()`, Express middleware, Rails `before_action` | Authorization chain, redirect targets |
| HTTP interceptor / filter | e.g., `intercept()`, Rack middleware, Axios interceptor | Error handling branches, next-handler chains |
| Component / view lifecycle | e.g., `ngOnInit()`, `useEffect()`, `mounted()` | Service calls, subscriptions, template bindings |
| Service / controller action | The public method called by the consumer | HTTP calls, state updates, error handlers |
| State flow | The action/event trigger | Reducers, effects, selectors, subscriptions |

### What to Capture

Capture only decisions that change behavior:
- Gate conditions (`if`, `switch`, guard outcomes).
- Async boundaries (`await`, observable chains, interceptors).
- Side effects (state updates, redirects, navigation, logout).

Omit straight-line code with no branching -- only include nodes where the flow forks, merges, or has a visible side effect.

### Depth Limits

- **Stop tracing** when you reach a side effect (state update, navigation, API call, error throw) or a service/layer boundary.
- **Do not trace into** utility/helper functions unless they contain a decision point (branch, error condition).
- **Do not trace into** trivial error handlers that just log and re-throw.

### Labeling

Keep labels concrete and code-facing (method names, route names, status codes). Each node must have a D2 comment with the source file path so viewers can jump to the implementation, e.g. `# src/app/core/guards/auth.guard.ts`.

## 3) Write Diagram Source

Create sources under `.claude/diagrams` with descriptive names:
- `.claude/diagrams/<flow-name>.d2`
- Ensure the directory exists: `mkdir -p .claude/diagrams`

### D2 Quick Reference

| Pattern | Syntax |
|---------|--------|
| Decision | `node: "label" { shape: diamond }` |
| Database/store | `node: "label" { shape: cylinder }` |
| Error highlight | `node: "label" { style.fill: "#f9e0e0" }` |
| Container | `group: "label" { child: "inner" }` |
| Ref into container | `group.child -> other` |
| Bidirectional | `a <-> b` |

### What NOT to Diagram

- Internal implementation of utility/helper functions (e.g., string formatting, array transforms).
- Trivial error handlers that just log and re-throw without branching.
- Third-party library internals -- stop at the call boundary (e.g., `httpClient.get()`, not RxJS internals).
- Getter/setter pass-throughs with no logic.

### Screen-Size Constraints

Diagrams must fit on a 1920x1080 screen without scrolling:

- **Default `direction: down`** — vertical flow is narrower and fits screens better.
- **Limit horizontal branches to 3-4 nodes** — if more, stack vertically or use containers.
- **Keep node labels short** — max ~30 characters per label. Use abbreviations for method names.
- **Use containers to group related nodes** instead of sprawling horizontally.
- **Split at ~15 nodes** — beyond that, create multiple focused diagrams rather than one massive one. Name the split files `<flow-name>-part1.d2`, `<flow-name>-part2.d2`, etc.
- **File size rule of thumb** — if the `.d2` source exceeds ~80 lines, consider splitting.

Use this template:

```d2
direction: down

# src/app/app.routes.ts
entry: "Route matched"

# src/app/core/guards/auth.guard.ts
branch: "canActivate()" {
  shape: diamond
}

auth: "Auth layer" {
  # src/app/core/guards/membership.guard.ts
  guard: "membershipGuard()"
  # src/app/core/resolvers/user.resolver.ts
  resolver: "resolve()"
  guard -> resolver
}

denied: "Redirect /login" {
  style.fill: "#f9e0e0"
}

entry -> branch
branch -> auth.guard: "session valid"
branch -> denied: "no session"
auth.resolver -> result

result: "Render component"
```

## 4) Render and Open

Render both SVG and PNG, then open for viewing:

```bash
bash scripts/render_and_open.sh .claude/diagrams/<flow-name>.d2 --open
```

The script uses a local `d2` binary if available, otherwise falls back to `npx -y terrastruct-d2-bin`. Outputs are placed next to the `.d2` source. Omit `--open` to render without opening.

If the script exits non-zero, read the error output and consult the troubleshooting section below. Fix the `.d2` source and re-run.

After rendering, confirm outputs exist: `ls -lah .claude/diagrams/<flow-name>.*`

### D2 Syntax Troubleshooting

Common errors and fixes:

| Error message / symptom | Cause | Fix |
|------------------------|-------|-----|
| `unexpected token` near a label | Unescaped special characters in label | Wrap label in double quotes: `node: "my label"` |
| `connection references must reference a board's connection` | Arrow inside a container referencing an outside node | Move the connection outside the container block, use `container.node -> outside` |
| `"x" is not a valid shape` | Typo in shape name | Valid shapes: `rectangle`, `diamond`, `cylinder`, `circle`, `oval`, `hexagon`, `queue`, `page`, `package`, `class`, `stored_data`, `person` |
| Diagram renders but labels overlap | Too many nodes at the same level | Add containers to group nodes, or split the diagram |
| `only one of (x, y) can be set to a reserved keyword` | Duplicate node ID or reserved word used as ID | Rename the node to avoid D2 reserved words (`label`, `shape`, `style`, `near`, `icon`, `constraint`, `direction`) |
| Semicolons cause parse errors | D2 does not use semicolons | Remove all `;` characters |
| Edge label not showing | Wrong syntax for edge label | Use `a -> b: "label text"` (colon after the target) |

## Success Criteria

Before handing back to the user, verify:

- [ ] Every node has a `# src/...` comment pointing to its source file.
- [ ] The rendered diagram fits on a 1920x1080 screen without scrolling.
- [ ] Node count is at most ~15 per diagram file; split if exceeded.
- [ ] No utility function internals or trivial error handlers are included.
- [ ] The `.d2` source, `.svg`, and `.png` all exist in `.claude/diagrams/`.

## Output

- Absolute paths to all generated files (`.d2`, `.svg`, `.png`).
- Brief summary of the flow modeled: entry point, key decision points, and terminal states.
- Whether the viewer opened successfully.
