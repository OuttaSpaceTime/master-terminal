---
name: scope-first
description: Front-load scope before any multi-file refactor. Produces a short scope contract — files to touch, exact behavior changes, what will NOT change — and waits for explicit user sign-off before any edits. Use when the user asks for a refactor, rename, extraction, or any change likely to touch more than two files. Trigger on "refactor X", "rename X across the codebase", "extract X into Y", "clean up X", "/scope-first", or any request where scope creep is a risk. Distinct from /plan (full sequenced strategy) and /sketch (draft diffs) — this is lighter-weight: just the scope contract, no diffs, no implementation plan.
---

# scope-first

Produce a scope contract for a refactor and wait for explicit user sign-off before editing anything. Lightweight — no diffs, no implementation plan. The goal is to eliminate scope creep at the start, not to design the change.

## When to use

- Refactors touching >2 files
- Renames or API changes with callers across the codebase
- "Clean up X" requests where the boundary isn't obvious
- Test suite reorganizations
- Any change where the user has previously pushed back on over-editing

Not for: single-file edits, bug fixes with a clear single locus, or small well-understood changes — use /sketch or direct edits instead.

## Output: the scope contract

Produce exactly these four sections. Keep it under 200 words total.

### Goal

One sentence restating what the user asked for, in your words. This catches misunderstandings before they cost time.

### Files I will touch

Bulleted list of concrete paths. If you don't know yet, list the ones you're confident about and mark the rest as "TBD — will confirm after reading X".

### Behavior changes

Bulleted list of the exact behavior deltas. Focus on observable changes (API surface, return values, side effects), not internal restructuring. If the user asked for a pure refactor, this section should say "None — behavior preserved".

### What I will NOT change

Bulleted list of adjacent things you might be tempted to touch but will leave alone. Examples: shared helpers, unrelated tests, style/formatting, nil guards, deprecation cleanup, imports beyond what's strictly needed. This section is the most important one — it is the explicit anti-scope-creep commitment.

## After the contract

Stop. Wait for the user to confirm or amend the scope. Do not edit anything until they sign off.

If during implementation you notice a tempting adjacent change:
- Stop.
- Surface it to the user.
- Do not bundle it in.

If the user approves an expansion mid-implementation, update the contract in-place (add to "Files I will touch" / "Behavior changes") before editing the new code. The contract stays current.

## Style

- No emoji.
- No preamble ("Here is the scope contract..."). Start directly with the Goal section.
- No trailing summary. The contract is the output.
