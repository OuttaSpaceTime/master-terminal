---
title: Solveit Method
tags: [methodology, agents, skills, ai, learning]
created: 2026-04-21
updated: 2026-04-21
---

# Solveit Method

Reference notes on Solveit — the platform and methodology from Jeremy Howard, Eric Ries, and Answer.AI (fast.ai). Kept here because its ideas are the main reference point for how our agent skills are designed to keep the human as the agent.

## One-line definition

AI-assisted literate programming: a single document combines executable code, notes, and AI dialog, with the human driving in deliberately small, verifiable steps.

## Philosophy

- **Polya, not vibes.** Built on George Polya's 1945 *How to Solve It* — Understand → Plan → Carry out → Look back. Explicitly framed as the opposite of vibe coding.
- **Small, verifiable steps.** Write 1–2 lines, inspect output, only then proceed. Combine into larger functions after verifying parts individually.
- **Human is the agent.** Interface choices resist automation — code doesn't auto-execute, completions usually require explicit triggering, Learning mode gives tiny suggestions instead of full solutions.
- **Dialog is editable state, not a log.** You rewrite past AI turns, hide irrelevant history, pin critical context. Counters the auto-regressive failure mode where one AI mistake makes the next more likely.
- **Shared context.** The AI sees exactly what the human sees — notes, code, outputs, prompts, in one document.
- **Reflection is first-class.** Every session ends with "look back": what was learned, what heuristic generalizes.
- **Anti-slot-machine.** One-shot agentic flows (fire prompt → come back in 30 min → keep or discard) are structurally variable-reward loops. Solveit's tight cycle is designed to deny that reward schedule.

## Platform in Jeremy's own words

Solveit combines: ChatGPT + Jupyter/nbdev + Monaco (VS Code's editor) + a persistent Linux VPS + Claude-Code-equivalent tools + a persistent terminal. The parts he claims are genuinely novel:

1. **MCP-but-simpler** — any Python function in the kernel becomes an AI tool via `` & `fn` ``.
2. **Live-variable reference** — the AI can be handed a pointer to a real runtime Python object (optional per message, so context isn't blown).
3. **Full metaprogramming of the dialog** — code or AI tools can rewrite the notebook structure (add headings, reorganize messages, find-and-replace across cells).
4. **Context editing as the correction primitive** — you edit the AI's prior turn in place rather than saying "that's wrong, try again." Stated as a *should*, not just a *can*.
5. **Collaborative live editing** of a dialog.

## Three message types

A Solveit "dialog" is a notebook blending three message types in one document:

- **Code** — runs in a per-dialog persistent Python kernel.
- **Note** — markdown, collapsible by heading level (1–6), with per-section token counts.
- **Prompt** — AI turn. Streaming, stoppable mid-stream, editable after the fact.

## UI mechanics worth remembering

- **Keyboard-first Selection Mode.** `A/B` add above/below, `X/C/V` cut/copy/paste messages, `Cmd+Shift+J/K/L` switch mode, `Enter` edit, `Cmd+Enter` run/submit, `W` extracts code from an AI response into a real code cell.
- **Pin (`P`) / Hide (`H`).** Pinned messages always enter AI context; hidden stay in the document but are invisible to the model. Old messages auto-drop when context fills.
- **Modes.** *Learning* (AI probes background, small suggestions), *Concise* (direct, minimal), *Standard* (verbose LLM default).
- **Symbol Browser** (`Ctrl+Shift+V`) — live view of kernel state: variables, functions, markdown headings as an outline.
- **Export flag** (`E`) — mark code cells for export; the dialog becomes a reusable `.py` module.
- **Publish** — read-only Solveit-native page preserving layout, outputs, folded sections. Append `.html` for a blog view.

## Typical session flow

1. Write a **note** restating the problem in your own words (Polya step 1).
2. Prompt the AI — usually asking for the *next small step*, not a full solution.
3. Extract the code (`W`), run it, inspect the output inline.
4. Add a note on what you learned or a surprising result.
5. If the AI went sideways, *edit its turn* or delete the branch — don't argue with it.
6. Collapse solved sub-problems under headings and move on.
7. Finish with a "look back" note — alternatives, generalizable heuristic.

## What users report in practice

- Exploration takes longer; understanding is much deeper; you own what you ship.
- Several experienced devs (25 years, in one case) report it changed how they think, not just what they ship.
- A typical loop: "I use the AI less and less the more I use SolveIt."
- Legitimate counter-view (HN): top-down workflows — declare high-level, let AI build a typed construct, drill into it — also work for some devs/tasks. Both approaches valid.

## Applicability to skill design

This is the reason the page exists — what to port into our own agent skills.

### Principles we've adopted or plan to

- **Small steps, forced pauses.** No checkpoint that hands off to a long unattended run.
- **Human-as-agent.** Skills ask before deciding, never silently pick a direction on ambiguity.
- **Predict-first.** When walking code with the dev, ask what they expect *before* revealing — turns narration into mental-model building.
- **Correction primitive.** When the dev pushes back, edit the prior artifact statement in place and re-derive downstream. Don't append contradictions.
- **Running ledger.** A single top-of-artifact state block (Known / Assumed / Open / Decided) that every checkpoint updates — the skill's equivalent of Solveit's Symbol Browser.
- **Probe mode.** Portable analog of Solveit's live kernel: when reading is ambiguous, run a small read-only command and cite the output, not the code. Moves findings from Assumed → Known.
- **Look Back coda.** Pólya step 4 at the end of every substantial skill run — what was surprising, what heuristic generalizes, what would unblock faster next time. Compounds across reruns in the same area.
- **Export tagging.** Mark findings that must reach downstream consumers (e.g. `[→plan]`) so the artifact can be detailed without drowning the handoff.
- **Anti-slot-machine rule.** No skill step should rely on variable-reward batching (prompt → wait → hope).

### Design questions to consider for future skills

- Does the skill have a running ledger, or does it just append?
- Does it ever force the user to predict before revealing?
- Is there a way to run a probe when a finding is ambiguous, or does the skill just quote code?
- Does it end in a Look Back / reflection block?
- Can the user edit a prior statement and have the skill re-derive from there?
- What's the skill's equivalent of Pin / Hide?
- Does the skill announce a mode (Learning / Standard / Concise) up front?

### Where this lives in our tree

Scout implements the bottom-up Solveit variant (see `home/dot_agents/skills/scout/SKILL.md`). Future skills (plan, diff-review, walkthrough, control-flow-trace) should treat the principle list above as a shared vocabulary — not a checklist, but a set of named moves to reach for.

## Sources

- fast.ai — *A New Chapter for fast.ai: How To Solve It With Code* (2024-11-07)
- Answer.AI — *Launching Solveit, the antidote to AI fatigue* (2025-10-01)
- fast.ai — *A Guide to Solveit Features* (2025-11-07)
- Chris Thomas — *The Human is the Agent: How SolveIt Changed My Programming Journey After 25 Years* (2025-09-24)
- Jonathan Whitaker — *What Is Solveit?*
- Hacker News thread on the Solveit launch — including Jeremy Howard's own platform-summary comment
