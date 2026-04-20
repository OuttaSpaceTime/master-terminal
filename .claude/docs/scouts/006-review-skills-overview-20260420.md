# Scout 006 — Review Skills: Richer Overview + Sharper Role Split

- **Date:** 2026-04-20
- **Branch:** main
- **Complexity:** Medium (two skills, multiple design decisions, shared references, optional d2 integration)
- **Scope:** Evolve `/review` and `/diff-review` so that (a) an orientation map lands before table drill-down, and (b) the two skills occupy clearly distinct developer intents.

## Intent (as stated)

> Both skills currently only produce tables for orientation. User wants a faster/better "map" before the detailed walk. Split the skills more: `diff-review` = understand the changes / walkthrough; `review` = feedback on implementation, correctness, architecture. Options raised: control-flow graph, D2, HTML page, chat-rendered diagram.

## Frame (post-CP1, user-confirmed)

- The richer overview lives in **`/diff-review` only** — `/review` does *not* get its own overview step.
- `/review` keeps its CP1 chain hint to `/diff-review`. That chain stays opt-in, as today.
- `/review` becomes purely judgment-oriented (findings, risks, merge readiness). It leans *harder* on the chain rather than re-implementing orientation.
- Primary goal: a developer opening `/diff-review` should grasp the *shape* of the change in ~15s before any per-file walkthrough, then have a clear path to drill deeper.
- Progressive disclosure is the governing principle: TL;DR → high-level map → per-hunk walk.

## Skill State Today (ticket-defined + code-verified)

- `/diff-review` CP1 produces two tables: **Diff Overview** (File | Type | Lines ± | Area) and **Execution Flow Changes** (Phase | Files | What crosses the boundary). Then drills per-hunk in CP2. `home/dot_agents/skills/diff-review/SKILL.md:159-186`.
- `/review` has no CP1 overview table at all — CP1 is "Change Intent and Entry Flow" (prose + chain hint to `/diff-review`), CP2 is execution-flow reconstruction, CP3 is "Critical Hot Spots". `home/dot_agents/skills/review/SKILL.md:166-186`.
- The overlap risk is already acknowledged: CP3 of `/review` is **skippable** iff the developer first ran `/diff-review`. `home/dot_agents/skills/review/SKILL.md:181`.
- A `/d2` skill already exists that renders SVG/PNG from traced code flow and opens the viewer. `home/dot_agents/skills/d2/SKILL.md:1-167`.
- `/control-flow-trace` exists for execution-level deterministic traces with line references. `home/dot_agents/skills/control-flow-trace/SKILL.md:1-40`.
- `/walkthrough` exists for concept/learning reinforcement and is currently chainable from `/diff-review`. `home/dot_agents/skills/walkthrough/SKILL.md:1-50`.

## Checkpoints

### CP1 — Problem Frame
_(pending first exchange)_

### CP2 — Code Walkthrough & Questions

**Research synthesis (both passes converge on the same backbone):**

| Element | Tools (CodeRabbit / Greptile / Qodo) | Human methods (evidence) |
|---|---|---|
| Intent-first TL;DR | `Walkthrough` prose paragraph | Google step 1; Linux kernel patch philosophy |
| Intent-grouped file×purpose table | `Changes` table, bucketed (feature/fix/refactor/test/docs) | Google: biggest-logical-change first |
| Ripple / impact list | CodeSee Review Map innovation | Senior reviewers hand-draw this |
| Conditional diagram | Mermaid sequence diagram, gated on flow change | — |
| Size / time nudges | — | SmartBear/Cisco: 400 LOC / 60 min / 400 LOC·hr ceilings |
| Assumption / question panel | — | Springer EMSE 2025 (code review as decision-making) |
| Three-pass reading | — | Keshav adapted; MIT 6.005 |

**Mapping to `/diff-review` CP1 today** (`home/dot_agents/skills/diff-review/SKILL.md:159-186`):
- Diff Overview table ≈ element #2 but flat (no intent grouping).
- Execution Flow Changes table ≈ element #4 but unconditional text, not gated rendering.
- Elements #1, #3, #5, #6 are absent.

Low-hanging upgrade path: prepend TL;DR → group existing file table by intent bucket → add a ripple bullet list → gate D2 (or Mermaid inline) render on "flow actually changed" → conditional size nudge.

**Source artifacts (persisted separately for reference):** see conversation research output. Headline patterns from Tools pass ([1], [8] in that output): CodeRabbit docs — walkthrough paragraph + Changes table + optional Mermaid; Greptile — summary + per-file confidence + sequence diagram; Qodo `/describe` — `enable_semantic_files_types` buckets. Human-methods pass: Google eng-practices, SmartBear/Cisco study, Palomba TDR, Springer 2025.

### CP3 — Decision Gates

| # | Gate | Decision | Status |
|---|---|---|---|
| G1 | Overview medium | **HTML page** (`.claude/docs/diff-overviews/NNN-<branch>-YYYYMMDD.html`), `xdg-open`'d. ASCII inline fallback for headless. | DECIDED |
| G2 | HTML contents | TL;DR prose → intent-grouped `File \| Bucket \| Purpose` table → "touches but unchanged" ripple list → Mermaid (CDN) → size info | DECIDED |
| G3 | Chat output | Thin 5-line text summary: file count, ±LOC, TL;DR line, walk-order pointer, intent question. No full table in chat. | DECIDED |
| G4 | Diagram gating | Render only when cross-layer change OR new public entry point (mirrors `/d2` posture) | DECIDED |
| G5 | Walk-order default | Flip from leaf-first to **biggest-logical-change-first** (Google eng-practices) | DECIDED |
| G6 | Opinionated level | **Middle** — data-rich overview + walk-order flip + 400-LOC SmartBear nudge. Intent pre-fill / assumption panel → Later. | DECIDED |
| G7 | `/review` CP1 | Drop overview aspirations. Keep chain hint to `/diff-review`. | DECIDED |

**Anti-patterns:** no Mermaid inline in chat (Claude Code can't render it); don't rebuild D2 rendering (reuse existing); don't touch `/review` CP2-6.

**Pattern alignment:** HTML-page-to-xdg-open mirrors the existing `/d2` render-and-open ergonomic (`home/dot_agents/skills/d2/scripts/render_and_open.sh`). Reuse.

### CP4 — Risk & Verification

| # | Risk | Scenario | Mitigation (Now scope) |
|---|---|---|---|
| R1 | `xdg-open` fails on headless/SSH | SSH session with no `$DISPLAY`; renderer throws, dev sees error instead of overview | Detect `$DISPLAY`; if absent, print absolute HTML path + `file://` URI and skip auto-open. Test by running `DISPLAY= /diff-review`. |
| R2 | Mermaid CDN blocked airgapped | Corporate/offline machine — HTML opens but diagram block stays as raw text | On render, try CDN with short timeout; on fail, pre-render the diagram via `/d2` skill and inline the SVG. |
| R3 | Walk-order flip surprises existing users | Dev expects leaf-first walk, gets biggest-first | First-run notice ("Walk order now starts at the biggest logical change — name any file to override") + skill changelog comment. |
| R4 | Intent-bucket hallucination | LLM mis-buckets a file | Keep buckets small + mechanical (Feature / Fix / Refactor / Test / Docs / Config / Types / Other). Mark `Other` when unsure. Dev-correctable inline. |
| R5 | HTML artifact proliferation | `.claude/docs/diff-overviews/` grows unbounded | Flag as follow-up; simple keep-last-N prune can be Later. |

R1 and R2 are the only pre-ship blockers; both mitigations are cheap and fit inside Now scope. No risk invalidates a CP3 decision.

### CP5 — Mental Model & Handoff

**Ready for `/plan`.**

- **Now/Later/Out** — crisp (see below).
- **Blocking ambiguities** — none remaining. R1/R2 are implementation mitigations, not design ambiguities.
- **Affected files + test seams** identified:
  - `home/dot_agents/skills/diff-review/SKILL.md` — CP1 rewrite (`L159-186`), walk-order rule (`L226`).
  - `home/dot_agents/skills/diff-review/scripts/` — new helper (HTML render + open).
  - `home/dot_agents/skills/diff-review/references/intent-buckets.md` — new small reference.
  - `home/dot_agents/skills/review/SKILL.md` — CP1 cleanup (`L166-171`, strip overview aspirations, keep chain hint).
  - **Test seams (manual, no CI in repo):** headless run (`DISPLAY= /diff-review`), offline run (block CDN), tiny-diff case (diagram must be skipped), large-diff case (size nudge fires).

**Developer mental model for `/plan`:** CP1 becomes a two-channel output — terminal stays conversational (5-line summary + intent question), browser holds the rich map (TL;DR → table → ripple → diagram → size). The progressive disclosure is *physical* — the terminal literally cannot render the visual view, so the split is enforced by the surface itself.

## Open Questions

- (none blocking — R1 & R2 are handled inside Now scope)

## Scope Boundaries

**Now**
- New helper script under `home/dot_agents/skills/diff-review/scripts/` that writes a self-contained HTML (embedded CSS + CDN Mermaid, SVG-fallback path) and `xdg-open`s it (with headless fallback).
- Rewrite `diff-review/SKILL.md` CP1 (`L159-186`) for: TL;DR + intent-grouped table + ripple list + gated diagram render + size info + thin chat summary.
- Flip walk-order default at `diff-review/SKILL.md:226` to biggest-logical-change-first; add first-run change notice.
- Add 400-LOC size nudge (SmartBear ceiling) in CP1.
- New `home/dot_agents/skills/diff-review/references/intent-buckets.md` defining the 8 buckets (Feature / Fix / Refactor / Test / Docs / Config / Types / Other).
- Shrink `review/SKILL.md` CP1 (`L166-171`): remove any lingering overview language; keep chain hint verbatim.
- Deploy with `chezmoi -S home diff` → `apply`.

**Later**
- Intent pre-fill from commits/PR description with developer confirm step.
- Live assumption/question panel alongside Concerns in the notes file.
- 60-min and 400 LOC/hr ceiling prompts.
- Editor deep-links in the HTML table (`vscode://`, `cursor://`, nvim URL handler).
- Regenerate HTML on mid-session scope change (new files added).
- Keep-last-N prune for `.claude/docs/diff-overviews/`.

**Out**
- Changes to `/review` CP2-CP6 (findings, risk, verdict flow).
- Rebuilding D2/SVG rendering — reuse existing `/d2` skill.
- Stacked-diff / multi-PR / revision-matrix support (no local equivalent).
- A new dedicated overview skill (stays inside `/diff-review`).

> *If implementation discovers work outside these boundaries, it must STOP and ask — not silently expand scope.*
