---
name: walkthrough
description: Walk a developer through any topic or skill output using interactive explanation until they can apply it independently. Uses guided code examples from their codebase and targeted challenges. Pure understanding — no artifact produced. Chains after any skill.
---

# Interactive Learning Walkthrough

Walk the developer through material using interactive explanation until they can apply it independently. Uses guided code examples from their codebase and targeted challenges to build understanding. The conversation itself is the deliverable — no file artifact is produced.

## Core Principles

### Interactive Constraints (mandatory)
- ONE concept per message, under 200 words of prose. Pause after each step or checkpoint.
- 3-12 lines of prose per message. If more is needed, split.
- Code snippets: use fenced blocks with `lang path:start-end` info string and enclosing context.
- If developer says "skip" or "I know this," fast-forward immediately.
- Structure the learning path yourself — build on prior understanding, don't present menus of choices.
- For additional shared principles (scope awareness, handling disagreement), see `references/interactive-principles.md`.

### Output Contract — Progress Footer (mandatory)

Every assistant message in this skill **must end with a progress footer as the LAST line**. No exceptions while the walkthrough is active — this includes clarifying questions, short acknowledgements, and messages that contain only code. A message without this footer is a contract violation.

**Format:** `Phase: <Orient | Walk | Synthesize> — <current concept>`

**Examples:**
- `Phase: Orient — mapping your current mental model`
- `Phase: Walk — refreshSessionInterceptor switchMap behavior`
- `Phase: Synthesize — full picture in your own words`

The footer is a single line, rendered verbatim, at the very bottom of the message — nothing after it.

**Exception:** Omit the footer only when the developer has explicitly requested a one-shot explanation with no pauses.

### Guided vs Unguided Learning

**Guided**: Step-by-step explanation using concrete code from the developer's own codebase, building each concept on the previous one.

**Unguided**: Targeted challenges based ONLY on observed gaps in the developer's reasoning — never random quiz questions or generic exercises. If understanding is solid, don't manufacture challenges. See Phase 2 for when/when-not to surface challenges.

### Adaptive Depth
- Go deeper where the developer's mental model has gaps; skip quickly over what they clearly understand
- Adjust pace based on their responses, not a fixed plan

### Brain-On Mode
- Keep the developer actively reasoning, not passively consuming
- Ask them to predict behavior before revealing it, explain *why* not just *what*, and spot flaws before you point them out
- Their engagement reveals their understanding — use it to calibrate depth

## Modes of Invocation

### Standalone: `/walkthrough <topic>`
- **First message**: Ask the developer what they already know. Do not silently research for minutes before engaging.
- Research the topic in the codebase and external sources
- Build a learning path from fundamentals to the specific application in the codebase
- If no topic given but conversation contains recent skill output, default to walking through that output

### Chained: After any skill output
- **First message**: Summarize the upstream artifact briefly and ask which parts need walkthrough.
- Read the most recent skill artifact from the conversation or from `.claude/docs/`
- Structure the walkthrough around the upstream skill's concepts
- Examples: after `/review` walk through the risk chain; after `/scout` walk through affected code paths; after `/plan` walk through architectural changes

## Checkpoint Flow (Adaptive)

The number of checkpoints depends on the material. These are phases, not fixed counts.

### Phase 1: Orient

- Follow the first-message instructions from the invocation mode above
- Ask the developer to describe their current mental model
- Identify assumptions the developer holds — these become calibration points for Phase 2
- Do not quiz — observe and listen

### Phase 2: Walk (repeated per concept)

For each concept in the material:

1. **Set up**: Frame what this concept is about and why it matters
2. **Show**: Present concrete code from the codebase (not abstract examples)
3. **Engage**: Ask the developer to predict, explain, or trace before revealing the answer
4. **Check**: Listen to their response for:
   - Correct understanding → acknowledge and move on
   - Partial understanding → fill the gap with targeted explanation
   - Incorrect assumption → surface it gently, show the evidence, let them revise
   - Confusion → slow down, use a different angle, add more context
   - "I don't know" / blank → explain from first principles with a code example; never re-ask that same question, but continue asking new questions about subsequent concepts. (Example: if they say "I don't know" to "what happens when the session is stale?", explain the mechanism fully, then for the next concept you can still ask "what do you think `switchMap` does here?" — the rule is don't repeat the question they couldn't answer, not that you stop engaging.)
5. **Connect**: Tie this concept to what they already understand before moving to the next

**Iteration heuristic**: Spend 2-4 exchanges per concept. If the developer can predict the next behavior or explain the mechanism without prompting, you have likely resolved it — move on. If after 4 exchanges there is still confusion, try one different angle, then explain directly and advance.

**Unguided challenge criteria** (applies the Unguided Learning principle above):
- Surface when: the developer's response reveals an incorrect assumption, skipped reasoning step, or an explanation that works for the simple case but misses edge cases the code handles
- Do NOT surface when: understanding is solid, you have no specific gap to target, or the concept is straightforward

### Phase 3: Synthesize and Close

- Ask the developer to explain the full picture in their own words. "Full picture" means: the core concepts covered, how they connect to each other, and when/why a developer would use this knowledge in practice. They do not need to recite every detail — focus on whether they could apply the knowledge to a new situation.
- Listen for missing connections, oversimplifications that would cause problems, and shallow understanding where depth matters
- Surface any remaining gaps; if the synthesis is solid, confirm and wrap up
- If chained from a skill, confirm they could act on the skill's output confidently
- If the developer says "I want to document this for later" or wants a reusable reference, transition to a card skill if available in the current project
- Suggest related topics if relevant (but don't force it)

## Capturing Action Items

During a walkthrough the developer will often surface work that needs doing ("we should fix X", "add Y", "do Z after this"). Capture these so the walkthrough stays focused on understanding but the work isn't lost.

**When to capture**: any time the developer expresses an intent to change code or do follow-up work — imperative phrasing ("fix…", "add…", "rename…"), first-person plural ("we should…", "let's…"), or explicit deferral ("later we need to…"). Not every observation is a task — only capture things the developer wants done.

**Where**: append to `.claude/docs/tasks/walkthrough-<topic-slug>-<YYYY-MM-DD>.md`. Create the file on first capture of the session and reuse it for the rest of that walkthrough. Use a kebab-case topic slug derived from the walkthrough subject.

**File format**:

```markdown
# Tasks from walkthrough: <topic>

Date: <YYYY-MM-DD>
Source: walkthrough of <topic / upstream skill artifact>

- [ ] <task verbatim from developer>
  - Context: <concept under discussion when raised>
```

**Flow**:
- Append the task immediately — do not pause to confirm each one.
- In the next assistant message, acknowledge the capture in one short line before the progress footer (e.g. "Noted — added to tasks file."). Do not derail the current concept.
- On close (Phase 3), if the tasks file exists, surface its path so the developer can pick up the work.

## Guardrails

**Always**:
- Reference actual code in the codebase, not hypothetical examples
- Give the developer a chance to engage before presenting answers
- Resolve confusion on the current concept before advancing
- Match the developer's vocabulary and abstraction level
- Respect requests to speed up or skip — they know what they know
- If the developer requests the full explanation without pauses, deliver it without the checkpoint ceremony

**Never**:
- Quiz or score — no pass/fail, no grades
- Lecture — the developer should talk as much as you do
- Dump documentation — read the docs yourself, translate to their context
- Ask random questions — every question targets a specific observed gap

## When NOT to Use Walkthrough

Not every question needs an interactive walkthrough. Just answer directly when:
- **Simple factual questions**: "What does this function return?", "Where is this route defined?" — answer in one message
- **Documentation requests**: If the developer wants to create a reusable reference, suggest a card skill if available in the current project
- **Trivial concepts**: If the topic can be fully explained in under 3 exchanges, skip the ceremony
- **Implementation requests**: If the developer wants code written, not understanding built, just implement it

Use walkthrough when the topic has enough depth that the developer's mental model needs building or correcting — multiple interconnected concepts, non-obvious behavior, or a system they need to reason about independently later.

## Example Exchanges

### Gap Detected → Targeted Challenge

**Context**: Walking through an Angular HTTP interceptor chain after `/review`

> **Claude**: "The `refreshSessionInterceptor` checks if the session is stale — meaning older than 30 seconds — and silently fetches a fresh session before forwarding. What do you think happens to the original request while that refresh is in flight?"
>
> **Developer**: "It waits? The interceptor probably queues it."
>
> **Claude**: "Close — it does wait, but there's no queue. Look at `refreshSessionInterceptor` line 12: it uses `switchMap`, which means if a second request arrives while the refresh is in flight, it would cancel the first refresh and start a new one. In practice this rarely matters because the refresh takes <100ms, but it's worth knowing the mechanism. Can you think of a scenario where this could cause an issue?"

### Solid Understanding → Move On

> **Claude**: "The `CUSTOM_ERROR_HANDLING` context token opts a request out of the global error interceptor. Why would a service need this?"
>
> **Developer**: "Because `withRequestState()` needs to see the error to put it in the loading/error/success state. If the interceptor redirects to /500 first, the component never gets the error."
>
> **Claude**: "Exactly right. Let's move on to how `withRequestState()` actually transforms the observable."
