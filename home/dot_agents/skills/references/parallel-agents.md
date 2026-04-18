# Parallel Agent Discovery Protocol

Shared protocol for optional parallel agent discovery in interactive skills. Each skill defines its own agent roster, return format schemas, and phase placement in a skill-local `references/parallel-discovery.md`; this file defines the shared mechanics.

Relationship to `interactive-principles.md`: that file governs message style, pacing, and non-interactive mode. This file governs agent orchestration. Both apply simultaneously — parallel discovery doesn't change how checkpoints are presented.

## Complexity Gate

Use the skill's existing Proportional Depth classification to decide whether to spawn upfront agents:

- **Small** (single execution path, one layer, no design decisions): Single-pass discovery. No agents.
- **Medium+** (2+ execution paths, touches 2+ layers, or has design decisions): Spawn upfront agents from the skill's roster.

**Threshold tiebreaker:** When a skill uses file count as a secondary activation signal (e.g., 15+ files), changes in the 10-14 file range that clearly satisfy medium+ on the layer criterion should still spawn agents. When in doubt near the threshold, default to spawning.

**Override flags:**
- `--parallel` — force upfront agents regardless of complexity assessment.
- `--no-parallel` — force single-pass regardless of complexity assessment.

**Reassessment rule:** If single-pass discovery (small task, no agents) reveals wider ripple than expected after reading the entrypoint — e.g., a single file turns out to be a shared interceptor with many downstream consumers — upgrade to parallel mid-flight. Announce the upgrade with a one-line note before spawning.

## Upfront Agent Protocol

### When to spawn

Spawn all upfront agents at the start of the skill's discovery phase, before any interactive checkpoint begins. Each skill's SKILL.md specifies the exact phase placement.

### How to spawn

Use the Agent tool with `run_in_background: true` for parallelism. Spawn all roster agents in a single message so they run concurrently.

### What context each agent receives

Each agent starts cold with no conversation history. The spawn prompt must include:

1. **Task description** — the issue text, bug description, or feature request verbatim
2. **Scope boundaries** — what's in scope and out of scope (if already established)
3. **File hints** — any file paths already identified (entrypoint, mentioned in the issue, etc.)
4. **Agent mandate** — what specifically this agent should investigate (its role from the roster)
5. **Return format** — the exact schema this agent type must follow (from the skill's `references/parallel-discovery.md`)
6. **Constraints** — "Do not implement changes. Research only. Stay within the return format. Max 1000 words total."

### Announcement format

Before spawning, announce with one line per agent:

> Spawning 3 upfront agents: code-path tracer, impact mapper, in-flight change checker.

No detailed explanation needed — the announcement is for transparency, not discussion.

### What the main thread does while agents run

The main thread does not idle. It announces spawning, then begins reading the entrypoint and immediate context — enough to orient for synthesis, but not a full discovery pass. Do not re-read files the agents are likely to cover; focus on what only the main thread needs (issue context, existing scout artifacts, branch state).

### Agent failure or empty results

If an upfront agent returns nothing actionable (e.g., no in-flight branches found, or the agent timed out), note the gap in synthesis and cover it during the walkthrough via inline reads or an on-demand agent. Do not block on a failed agent — proceed with what the other agents returned.

## Synthesis Procedure

After all upfront agents return:

1. **Merge** — combine agent outputs into a single structured context. Group by topic (execution flow, affected files, risks) rather than by agent.
2. **Compress** — remove redundancy. If two agents identified the same file or risk, keep the higher-detail version.
3. **Resolve conflicts** — if agents disagree (e.g., tracer says file X is in the execution path, mapper says it's not impacted), note the conflict explicitly. Do not silently pick one.
4. **Flag gaps** — if no agent covered an area that the task description implies, note it as a gap for the walkthrough to address.
5. **Output** — a structured summary the checkpoints consume. Not raw concatenation of agent outputs.

The synthesis is internal working context — it is not presented to the developer as a separate deliverable. Checkpoints reference its contents naturally.

## On-Demand Agent Protocol

On-demand agents spawn during the interactive checkpoint phase when specific triggers fire. They are not pre-planned — they respond to gaps discovered during the walkthrough.

### Trigger conditions

1. **Developer question exceeds synthesized context** — the developer asks about a code path, file, or behavior that the upfront agents didn't cover and the main thread can't answer from what it has.
2. **Finding contradicts upfront agent** — something in the walkthrough conflicts with what an upfront agent reported. A fresh agent verifies which is correct.
3. **Developer requests unexplored code path** — the developer explicitly asks to explore something the upfront pass skipped.
4. **New risk needs independent verification** — a risk surfaces during discussion that needs a targeted check against the codebase.

### Decision rule: spawn vs. read directly

Spawn an on-demand agent when answering requires reading more than 3 files you haven't read, or when a finding needs independent verification from a fresh perspective. For a single targeted lookup (one file, one symbol, one quick check), read the file directly — an agent adds overhead without benefit.

### Mechanics

- **Agent-initiated with announcement.** The main thread announces intent before spawning: "Spawning an agent to check [specific thing]."
- **Max 1 concurrent on-demand agent.** Wait for the current one to return before spawning another.
- **Same return format constraints apply.** Use the most appropriate schema from the skill's `references/parallel-discovery.md`, or the generic on-demand schema below. Cap 1000 words.
- **Results incorporate inline.** On-demand agent findings fold into the current checkpoint discussion. They do not create a separate deliverable.

### Generic on-demand return schema

Use this when no upfront agent schema fits the on-demand question:

```
## Findings
- [finding] — path:line — confidence: high/medium/low

## Evidence
- [what was checked] — [what was found]

## Additional Notes
[free text]
```

### What on-demand agents are NOT

- Not a substitute for thorough upfront discovery. If on-demand agents fire repeatedly, the upfront roster may need expansion for this skill/task type.
- Not critique agents. Critique agents fire at defined phase transitions regardless of developer input. On-demand agents fire in response to gaps.

## Report-Only / Non-Interactive Mode

When running in report-only or non-interactive mode (subagent, explicit "give me the full report" request):

- **Full parallelism permitted.** Upfront agents and synthesis run as normal.
- **On-demand agents do not fire.** There is no developer loop to trigger them.
- **Critique agent still fires** (if the skill defines one). It operates on the skill's output, not on developer input.
- **The entire flow is: spawn → synthesize → produce artifact → critique → finalize.** No interactive pauses.

## Visibility

All agent activity is transparent to the developer:

- Upfront agent spawning: announced with one-line summary before spawning
- On-demand agent spawning: announced with specific reason before spawning
- Critique agent spawning: announced at the phase transition (if the skill defines one)
- Agent results: incorporated into the walkthrough naturally, not presented as raw agent output
- Mode selection: the skill's first message notes whether parallel discovery is active and why (complexity assessment or explicit override)
