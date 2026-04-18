# Parallel Agent Discovery for Skills — Scout Report

## Report Location
- Saved file: `.claude/docs/scouts/005-parallel-agent-skills-20260412.md`

## Problem Frame

**Today:** Scout, plan, and review skills run all discovery sequentially inline — reading files, tracing flows, building maps — while the developer watches and waits. Interactive checkpoints interleave exploration with walkthrough. Report-only mode is the same sequential pass without pauses.

**After:** Discovery can run upfront via parallel agents (code-path tracer, impact mapper, risk checker). Interactive checkpoints become walkthrough of pre-computed findings. On-demand agents spawn mid-checkpoint when the developer's questions exceed what the upfront pass covered. A complexity gate skips agents for small tasks.

**Branch state:** Clean — no implementation started. Greenfield skill authoring.

**Complexity:** Medium — touches 4 files (3 SKILL.md + 1 new reference), no code logic, but protocol design requires careful specification.

## Decision Gates

### Gate 1: Agent return format — `[DECIDED]`
- **Decision:** Structured with overflow (Option C)
- **Detail:** Each agent returns a fixed schema (affected files table, flow summary max 15 steps, open questions max 5, risk flags) with an optional "additional notes" free-text field. Total cap: 1000 words per agent. Schema differs per agent type.
- **Anti-pattern:** Do NOT let agents return free-form prose without structure — synthesis becomes unreliable.

### Gate 2: On-demand agent trigger conditions — `[DECIDED]`
- **Decision:** Agent-initiated with announcement (Option B)
- **Triggers:** (a) developer asks a question the synthesized context can't answer, (b) a finding contradicts an upfront agent's conclusion, (c) a new risk surfaces that needs independent verification.
- **Each spawn announced with a one-line note before it fires.**
- **Hard cap:** 1 on-demand agent active at a time.
- **Anti-pattern:** Do NOT spawn on-demand agents silently or spawn multiple simultaneously.

### Gate 3: Complexity gate signal — `[DECIDED]`
- **Decision:** Reuse Proportional Depth as-is (Option A)
- **Detail:** Small = single-pass, medium+ = parallel agents. Existing skill classification based on execution paths, layers crossed, decision points.
- **Override:** `--parallel` forces agents on any task. `--no-parallel` forces single-pass.
- **Reassessment rule:** If single-pass discovery reveals wider ripple than expected after reading the entrypoint, upgrade to parallel mid-flight.
- **Anti-pattern:** Do NOT use file count as the complexity signal.

### Gate 4: Reference import location — `[DECIDED]`
- **Decision:** Own "Parallel Discovery" section in each SKILL.md (Option B)
- **Detail:** 5-10 lines naming skill-specific agents, when they fire, reference to `../references/parallel-agents.md` for protocol.
- **Anti-pattern:** Do NOT inline the full protocol in each SKILL.md — shared mechanics go in the reference file.

## Scope Boundaries

### Now (in scope)
- New shared reference: `home/dot_agents/skills/references/parallel-agents.md`
  - Agent protocol mechanics (spawn, context handoff, return format schemas)
  - Synthesis procedure
  - On-demand trigger conditions and hard caps
  - Complexity gate rules and override flags
- New "Parallel Discovery" section in `home/dot_agents/skills/scout/SKILL.md`
  - Upfront agents: code-path tracer, impact mapper, in-flight change checker
  - Feeds into CP1-2 walkthrough
  - General on-demand protocol only (no dedicated critique agent — scout's interactive checkpoints surface gaps naturally)
- New "Parallel Discovery" section in `home/dot_agents/skills/plan/SKILL.md`
  - Upfront agents for Mode B discovery: entrypoint flow tracer, pattern reference reader, test infrastructure scanner
  - Critique agent after Step 13 (Draft Diffs)
  - On-demand triggers during checkpoints
- New "Parallel Discovery" section in `home/dot_agents/skills/review/SKILL.md`
  - Gate checks parallel with diff analysis
  - Upfront agents for large diffs (30+ files): per-feature-area batching
  - Critique agent after Step 9 (Architecture Gates)
  - On-demand triggers during CP2-5

### Later (deferred)
- Rewriting checkpoint text to assume upfront discovery (full restructure)
- Diff-review, walkthrough, or other interactive skills adopting the protocol

### Out (excluded)
- Changing the interactive checkpoint flow itself
- Adding flag-parsing logic (agent interprets from invocation args)

"If implementation discovers work outside these boundaries, it must STOP and ask — not silently expand scope."

## Risks

### Risk 1: Redundant context from sloppy synthesis
- **Scenario:** Synthesis doesn't compress well, main thread re-reads files agents already covered, inflating context.
- **Likelihood:** Medium
- **Blast radius:** Earlier context limit hits, truncated later checkpoints
- **Mitigation:** Hard caps on agent returns (800-1000 words each). Synthesis compresses to structured summary, not raw concatenation. Main thread trusts synthesis and doesn't re-read unless contradicted.

### Risk 2: Stale synthesis
- **Scenario:** Upfront agents run, then developer mentions recent changes that invalidate findings. Walkthrough presents stale information as current.
- **Likelihood:** Low
- **Blast radius:** Decision gates built on wrong assumptions, plan inherits flawed scout
- **Mitigation:** When developer contradicts a synthesized finding, main thread re-reads the specific file or spawns on-demand agent if contradiction is broad.

### Risk 3: Complexity gate misclassification
- **Scenario:** Task looks small but involves a shared module with wide ripple. Agents not spawned, single-pass misses impact.
- **Likelihood:** Low
- **Blast radius:** Scout undercovers, plan inherits blind spots
- **Mitigation:** (1) Single-pass reassesses complexity after reading entrypoint — upgrades to parallel if ripple is wider than expected. (2) Skill notes which mode it chose in CP1 output so developer can override early.

## Affected Files

| File | Impact | Change Intent |
|---|---|---|
| `home/dot_agents/skills/references/parallel-agents.md` | create | Shared agent protocol reference |
| `home/dot_agents/skills/scout/SKILL.md` | modify | Add "Parallel Discovery" section |
| `home/dot_agents/skills/plan/SKILL.md` | modify | Add "Parallel Discovery" section |
| `home/dot_agents/skills/review/SKILL.md` | modify | Add "Parallel Discovery" section |

## Test Seams

- No automated tests — these are markdown skill files
- Validation: invoke each skill on a medium+ task and verify agents spawn; invoke on a small task and verify single-pass; invoke with `--parallel` override and verify forced agent mode
- Verify `chezmoi -S home diff` shows expected changes before deploying

## Handoff

- **Status:** Ready for `/plan`
- **All gates resolved.** No open blockers.
- **Next action:** `/plan` to sequence implementation — reference file first, then per-skill sections.
