---
title: Solveit Method
tags: [methodology, agents, skills, ai, learning]
created: 2026-04-21
updated: 2026-04-29
---

# Solveit Method

Reference notes on Solveit — the platform and methodology from Jeremy Howard, Eric Ries, and Answer.AI (fast.ai). Kept here because its ideas are the main reference point for how our agent skills are designed to keep the human as the agent.

## One-line definition

AI-assisted literate programming: a single document combines executable code, notes, and AI dialog, with the human driving in deliberately small, verifiable steps.

## Philosophy

- **Polya, not vibes.** Built on George Polya's 1945 *How to Solve It* — Understand → Plan → Carry out → Look back. Explicitly framed as the opposite of vibe coding.
- **Small, verifiable steps.** Write 1–2 lines, inspect output, only then proceed. Corollary from Lesson 1: errors live in the last 2–4 lines you wrote, so a debugger is rarely needed.
- **Predict before run.** Stating the expected output before executing is the default, not a pedagogical mode. The *gap* between prediction and reality is the highest-value learning event in a session — log it as a finding ("predicted X, got Y, model of Z is wrong"), don't just note the result.
- **Empirical output beats reasoning.** When reading code and running it would both answer the question, run. Add a print, hit the REPL, log the value — then reason about what came back. Reading is a fallback when running is impossible.
- **Reproduce before fixing.** No patch without a reliable, minimal failure first. For bug fixes, write the failing test before the fix and confirm it fails for the right reason.
- **JRY before DRY.** Just Repeat Yourself until the duplication actually hurts — then extract. Premature abstraction freezes a design before its shape is known. Adjacent cleanup is logged, not bundled.
- **Human is the agent.** Interface choices resist automation — code doesn't auto-execute, completions require explicit triggering, Learning mode gives tiny suggestions instead of full solutions.
- **Dialog is editable state, not a log.** You rewrite past AI turns, hide irrelevant history, pin critical context. Counters the auto-regressive failure mode where one AI mistake makes the next more likely. Edit, don't re-prompt.
- **Context engineering over agentic autonomy.** Manual context curation (pinned notes, scraped docs, summary hierarchies, handoff notes between sessions) consistently outperforms long unattended agent loops. Most users under-invest in context by an order of magnitude.
- **Shared context.** The AI sees exactly what the human sees — notes, code, outputs, prompts, in one document.
- **Reflection is first-class.** Every session ends with "look back": what was learned, what heuristic generalizes, what the human can now do that they could not before.
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

### Principles we've adopted

- **Small steps, forced pauses.** No checkpoint that hands off to a long unattended run.
- **Human-as-agent.** Skills ask before deciding, never silently pick a direction on ambiguity.
- **Predict-first as default.** Asking what the user expects *before* revealing the answer is the floor, not an opt-in pedagogical mode. The user's escape hatch is `skip` / `I know this`, not the agent's discretion.
- **Empirical probes preferred.** When running and reading would both answer the question, run. Skills split probe lists into Executable (preferred) vs Inspectional (fallback).
- **Reproduction gate.** No patch contract without a reliable failure in the ledger. For bug fixes, the validation step is a test that currently fails for the right reason.
- **No bundling.** Adjacent cleanup, refactors, or "while we're here" improvements get logged under `Open`, not folded into the patch.
- **Verify, don't guess.** Flag names, config keys, defaults, and API semantics get checked against docs/source/`--help`/LSP, not invented. If unverifiable, say so out loud.
- **Correction primitive.** When the dev pushes back, edit the prior artifact statement in place and re-derive downstream. Don't append contradictions.
- **Running ledger.** A single top-of-artifact state block (Known / Assumed / Open / Next Probe) that every checkpoint updates — the skill's equivalent of Solveit's Symbol Browser.
- **Look Back coda.** Pólya step 4 at the end of every substantial skill run — what was learned, what the user can now do that they could not before, what heuristic generalizes, what command became the reliable probe.
- **Anti-slot-machine rule.** No skill step should rely on variable-reward batching (prompt → wait → hope).

### Design questions to consider for future skills

- Does the skill have a running ledger, or does it just append?
- Is prediction the *default* before revealing, with `skip` as the escape — not the other way around?
- Does it prefer executable probes over reading-and-reasoning?
- Does it require a reproduction before proposing a fix?
- Does it forbid bundling adjacent changes?
- Is there a verify-don't-guess rule for APIs and config?
- Does it end in a Look Back / reflection block that names what the user *now knows*?
- Can the user edit a prior statement and have the skill re-derive from there?
- What's the skill's equivalent of Pin / Hide for context?

### Where this lives in our tree

`solveit-nvim` (`home/dot_agents/skills/solveit-nvim/SKILL.md`) is the most direct port of the method to ordinary project work — coaching-only by default, capability-laddered (Manual → Selection Push → Ambient Pull → Guided Steering), patch contract gated on reproduction. `forge` (scout + plan unified) and `code-review` (replaces diff-review/review) are the other current skills that lean on the same vocabulary. Treat the principle list above as a shared vocabulary — not a checklist, but a set of named moves to reach for.

## Sources

- fast.ai — *A New Chapter for fast.ai: How To Solve It With Code* (2024-11-07)
- Answer.AI — *Launching Solveit, the antidote to AI fatigue* (2025-10-01)
- fast.ai — *A Guide to Solveit Features* (2025-11-07)
- Chris Thomas — *The Human is the Agent: How SolveIt Changed My Programming Journey After 25 Years* (2025-09-24)
- Jonathan Whitaker — *What Is Solveit?*
- Hacker News thread on the Solveit launch — including Jeremy Howard's own platform-summary comment
