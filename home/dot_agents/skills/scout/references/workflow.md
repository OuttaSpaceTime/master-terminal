# Feature Scout — Reference Details

## Walkthrough Evidence Requirements

For each major checkpoint, include at least one `Walkthrough Evidence` block tied to concrete evidence.

Each block must include:

- evidence type: `requirement`, `behavior trace`, `module map`, `contract`, `test`, or `decision gate`
- location: `path:line` when code, config, docs, or tests exist
- evidence path: `path:line -> path:line -> ...`
- short excerpt trimmed to the relevant lines
- interpretation explaining what is known
- unknowns explaining what still needs to be learned

Source constraints:

- Use excerpts only from the actual repository, issue text, linked project docs, or user-provided material.
- Do not invent requirements, constraints, or behavior.
- Keep excerpts short and high-signal.
- Do not include code-level implementation proposals in early checkpoints.

## Affected Code Walkthrough Requirements

- Walk the affected code before finalizing scoping decisions.
- Trace in interaction order where possible:
  - entrypoint
  - coordinator/controller/container
  - domain/service logic
  - persistence or integration boundary
  - existing tests or missing test seams
- Include both changed and adjacent unaffected code when the adjacent code controls behavior, invariants, or extension points.
- Explain current behavior first, then expected behavior, then unresolved gaps.
- Call out what the ticket assumes that the code does not obviously support yet.
- Prefer concrete repository paths. If exact paths are unknown, list the discovery commands used and the closest boundary found.

## Impacted Files Inventory

After the code walkthrough, create two inventories:

- affected files, components, services, modules, contracts, and integrations
- affected tests, checks, and verification commands

For each entry, capture:

- current responsibility
- why it is impacted
- high-level change intent
- risk level

Walk touchpoints in interaction order, not alphabetical order.

## Decision Gate Selection

Select only the highest-impact gates, usually 3-6. Always include:

- acceptance-criteria and business-rule alignment
- minimal-first scope boundary
- pattern alignment — compare each proposed approach against codebase patterns
- test strategy — what patterns exist, what scenarios need coverage

Add other gates only when truly relevant:

- framework or library capability choice
- security and permission model
- data ownership and source of truth
- compatibility or migration concerns
- failure semantics

For each gate, capture:

- **status:** `[DECIDED]`, `[OPEN]`, or `[ASSUMED]`
- question being decided
- selected direction
- alternatives considered
- rationale and tradeoffs
- **anti-pattern:** what the WRONG approach would be
- confidence level
- whether required for `Now` or can wait

## Probe Patterns

Probes are small, read-only commands run during CP2 to turn an **Assumed** finding into a **Known** one. See the `Probe mode` block in SKILL.md for when to run them; this page lists common idioms.

Common probe idioms by layer:

- **Runtime value** — `console.log` / `pp` / `dbg` / Python repl / debugger breakpoint with print
- **Config source** — `git show HEAD:<config>`, `env | grep <key>`, framework config dump
- **Data shape** — single-row SQL `LIMIT 1`, API call piped to `jq keys`, fixture inspection
- **Call-site mapping** — `rg <symbol>`, LSP references, `git grep`, IDE "find usages"
- **Hit confirmation** — add a temp log line, re-run the failing command/test once, observe, revert
- **History** — `git log -p -- <path>`, `git blame -L`, recent commits touching the area

Rules:

- Cite the probe command verbatim in the artifact so the dev can re-run it.
- Probes must be read-only. If a probe requires inserting instrumentation, it must be reverted in the same turn.
- Never probe shared/production systems without explicit confirmation.
- One probe per ambiguity. If two probes are needed, the first one should have collapsed the question — reconsider.

## Look Back Template

Inserted at the bottom of the scout artifact under a `## Look Back` heading. Mandatory in Learning mode, recommended in Standard, single-sentence in Concise.

```markdown
## Look Back

**Surprising:** <one finding not predicted by ticket or first-glance reading>

**Heuristic:** <one sentence a future scout in this area should know>

**Next-time unblocker:** <tool, doc, probe, or test harness that would have saved time>
```

When the scout explicitly found nothing surprising, write `Surprising: none — confirm scout depth was adequate.` Do not skip the field.
