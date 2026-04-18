---
name: diff-review
description: >
  Understand your current git changes through interactive walkthrough. Shows actual diffs
  alongside execution flow, data flow, types, and invariants. Surfaces concerns and flaws
  noticed during the walk — interactively, not as a verdict. Opens live discussion at any
  point — agreed changes, concerns, and questions are captured to a notes file on approval.
  Use when you want to understand what your changes do, trace data paths, surface invariants,
  flag anything noticed along the way, or discuss changes before committing. NOT for
  merge readiness or exhaustive bug reports (use /review for that). Trigger on: "walk me
  through my changes", "what does this diff do", "review my changes with me", "let's
  discuss what I changed", /diff-review, or any request to understand or annotate
  current git changes.
---

# Diff Review

Understand what your changes do before deciding what to do next. The session succeeds when
you can explain the data path through your own changes without looking at the diff — and
have a record of anything worth following up on.

Comprehension naturally surfaces things worth noting: type gaps, implicit contracts, design
inconsistencies, footguns the type system won't catch. These are **concerns** — not verdicts.
They live in Checkpoint 3, alongside invariant analysis, because they arise from the same
question: *"what does usage assume that the code doesn't guarantee?"*

## Interactive Constraints (mandatory)
- ONE concept per message, under 200 words of prose. Pause after each step or checkpoint.
- 3-12 lines of prose per message. If more is needed, split.
- Code snippets: use fenced blocks with `lang path:start-end` info string and enclosing context.
- If developer says "skip" or "I know this," fast-forward immediately.
- For additional shared principles (scope awareness, handling disagreement), see `references/interactive-principles.md`.

## Output Contract — Progress Footer (mandatory)

Every assistant message in this skill **must end with a progress footer as the LAST line**. No exceptions while the interactive flow is active — this includes clarifying questions, short acknowledgements, and messages that contain only code. A message without this footer is a contract violation.

**Format:**
- Multi-hunk file walk: `Step 2/5 · Checkpoint 2/4 — services/task.service.ts: hunk 1/3`
- Single-hunk file walk: `Step 2/5 · Checkpoint 2/4 — services/task.service.ts`
- File-level invariants/concerns message: `Step 2/5 · Checkpoint 3/4 — services/task.service.ts: invariants`
- Without file context: `Checkpoint 1/4 — Diff Overview`

Rules:
- **`Step M/N` is the file counter.** M is the current file index, N is the total number of files being walked. The hunk counter is NEVER in the `Step M/N` slot — it lives in the trailing descriptor as `hunk K/L`.
- **File index stays fixed across sub-messages for the same file.** The trailing descriptor changes (`hunk 1/3` → `hunk 2/3` → `invariants` → `concern`). The file index also carries over from CP2 (per-hunk walk) into CP3 (file-level invariants/concerns) for the same file — advance the file index only when moving to a new file, regardless of which checkpoint the message belongs to.
- **Discussion does not advance the counter.** If the developer interrupts to explore or ask follow-up questions, the footer stays on the current step until the developer explicitly advances. This rule is the skill-specific instantiation of the shared returning-from-discussion protocol — where the generic rule says "re-state file, checkpoint, step" on resume, this skill re-states `file, checkpoint, hunk K/L` (or `file, checkpoint, invariants` for CP3 messages).
- **Single-hunk files** collapse to the short form — no `hunk 1/1` noise.
- **Hunk message that blows the budget.** If the diff + behavior summary for a single hunk exceeds the 3-12 line budget, split into two sub-messages with the file and hunk index unchanged: first message carries the diff with descriptor `hunk K/L — diff`, second carries the behavior summary with descriptor `hunk K/L — behavior`. The hunk counter does NOT advance between them. Same rule as governors splitting off into their own sub-message.

The footer is a single line, rendered verbatim, at the very bottom of the message — nothing after it.

**Exceptions:** Omit the footer only when the developer has explicitly opted out of the interactive flow — trivial-diff fast path, or an explicit "give me a one-message summary" request.

## Core Stance

- Checkpoint 2: show what the code does. Checkpoint 3: show what the code assumes and where those assumptions aren't enforced.
- A concern is "I noticed this while tracing the data — worth a look?" Not "this is wrong."
- Discussion is first-class: never push through a checkpoint when the developer wants to explore.

---

## Input Modes

| Mode           | Shorthand | Git command(s)                                           |
|----------------|-----------|----------------------------------------------------------|
| `conversation` | `c`       | Files Claude touched this session (see Mode Detection)   |
| `staged`       | `s`       | `git diff --cached`                                      |
| `unstaged`     | `u`       | `git diff`                                               |
| `main`         | `m`       | `git diff main...HEAD` + `git diff HEAD` (all uncommitted) |

**Default:** `conversation`. If conversation yields no changed files, fall back explicitly.

Accept a mode as the first argument: `/diff-review staged`, `/diff-review main`, etc.
If the argument is unrecognized, ask — do not guess.

### Mode Detection: Conversation Changes

1. Collect files from Write/Edit/MultiEdit tool calls this session.
2. Verify actual changes: `git diff HEAD -- <file>`, `git diff --cached -- <file>`,
   `git status -- <file>`.
3. Cross-check full working tree (`git diff --name-only`, `git diff --cached --name-only`).
   Note changed files not touched in conversation — developer may want to include them.
4. **Fallback:** If step 1 yields no files, state it and show all uncommitted changes.
5. Do NOT use `git log --since` — reflects commits, not unsaved edits.

---

## Scope Limits

- **Trivial diff** (rename-only, formatting, single-line constant): offer a one-message
  summary, skip the checkpoint ceremony. Ask whether to proceed.
- **Large diff** (40+ files or 1500+ lines): show the overview table, ask the developer
  to name the 3-5 most important files, walk only those. Note skipped files.
- **Mixed unrelated changes**: surface this before starting. Ask whether to walk together
  or focus on one area.
- **Staged mode, no staged changes**: state this clearly, ask whether to walk unstaged instead.

---

## Discussion and Capture — Available at Any Point

The developer can stop and discuss at any moment — not gated to checkpoint 4.

- Drop checkpoint pressure. Treat it as open conversation.
- **Returning from discussion (mandatory):** When discussion ends and the developer
  wants to continue the review, explicitly state what you are returning to — the same
  file, same checkpoint, same step — and ask the developer to confirm before continuing.
  Never silently resume or advance. Example: "Back to CP2 — we were on `file.ts`
  (3 of 7 files reviewed). Continue with this file, or move to the next?"
- **Planned changes** (things the developer decides to make) → "Planned Changes"
- **Concerns** (flagged observations approved for tracking) → "Concerns"
- **Unresolved questions** → "Open Questions"
- When the developer says "save this": propose the exact text, wait for confirmation,
  then append to the notes file. Never write without approval.

---

## Notes File

**Path:** `.claude/docs/diff-notes/YYYYMMDD-<branch>.md`
- `<branch>` from `git rev-parse --abbrev-ref HEAD`; replace `/` with `-`.
- Detached HEAD: use `git rev-parse --short HEAD`.
- Create with `mkdir -p` after the developer states their intent (Checkpoint 1, step 5).
- **Non-blocking:** if creation fails, state it and continue. Offer to retry at the end.
- Update Progress Tracker after each file status change — do not batch.

```markdown
# Diff Notes: <branch> — <YYYY-MM-DD>

## Progress Tracker

| File | Status | Notes |
|------|--------|-------|
| path/to/file.ts | ⬜ pending | |
| path/to/file.ts | 🔄 in progress | |
| path/to/file.ts | ✅ reviewed | |
| path/to/file.ts | ⏭ skipped | reason |

Status key: ⬜ pending · 🔄 in progress · ✅ reviewed · ⏭ skipped

Use the exact emoji indicators above — not plain text like "pending" or "reviewed".

## Concerns
<!-- Observations from Checkpoint 3. Added on approval. -->
<!-- Each entry: what it is, file:line, why it matters. -->

## Discussion Points

## Planned Changes

## Open Questions
```

---

## Checkpoint Flow

### Checkpoint 1/4: Diff Overview

1. Run the git command(s) for the selected mode.
2. Produce the **Diff Overview table**: File | Type | Lines ± | Area
   - Type: `modified`, `added`, `deleted`, `renamed`
   - Area: inferred layer or feature (e.g. `inbox UI`, `routing`, `shared`)
3. State: N files changed, rough ±line count, areas touched.
4. **Execution Flow Changes table.** Before the per-file walk, establish the high-level
   mental model of the change and its effects on control flow. Dense table form — no
   code excerpts (those belong in CP2):

   ```
   | Phase | Files | What crosses the boundary |
   |-------|-------|---------------------------|
   | request entry | src/guard.ts | new claim-validation check |
   | session setup | src/session.service.ts | tightened timeout contract |
   | ...   | ...   | ...                       |
   ```

   Purpose: give the developer the cross-file mental model before drilling into per-file
   hunks in CP2. **Skip to a one-line summary** for trivial diffs or small diffs
   contained within a single layer.
5. If large, propose a walk order and ask for confirmation.
6. Ask: "What was the intent behind these changes?" Wait — it shapes walkthrough depth
   and what concerns in Checkpoint 3 are worth flagging.
7. After receiving the intent: create the notes file with all files `⬜ pending`,
   state the path. If creation fails, note it and continue.

---

### Checkpoint 2/4: Change Walkthrough

**Purpose: understand what the code does. No concerns here — those go in Checkpoint 3.**

**Resume protocol (mandatory):** Before walking any file, read the Progress Tracker.
Only walk files marked `⬜ pending` or `🔄 in progress`. This is the single source of
truth for where the session left off — after discussion, after interruption, always.

**Per-hunk rhythm.** Each hunk of a changed file becomes its own step. Multi-hunk files
walk across multiple messages. The file index in the footer stays fixed across all of a
file's hunks; the `hunk K/L` sub-counter advances. Single-hunk files collapse to a normal
step (no `hunk 1/1` noise). Mark the file `🔄 in progress` before showing its first hunk.

**Status-marking rule:** NEVER mark a file `✅ reviewed` unless (1) **every** hunk of
that file has been shown to the developer in this exchange, and (2) the developer
explicitly confirmed they are done with it. Any forward-moving response ("next", "good",
"continue") counts as confirmation. Silence or further discussion means the file stays
`🔄 in progress`. A file with any un-walked hunks cannot be marked `✅`, even on forward
confirmation — advance to the next hunk instead. Violating this rule invalidates the
review.

For each hunk:
1. Name the file, the hunk's position (`hunk K/L`), and the symbols it touches.
2. Show the actual diff for this hunk — trimmed to ≤3 lines of unchanged context.
   (See `references/diff-outline-format.md` for the full format.)
3. One-to-three sentence behavioral summary: what this hunk changes, where in the flow,
   data in → out.
4. **Adjacent governors inline only when this hunk needs them.** If unchanged code
   nearby governs the behavior of this hunk, pull in a short excerpt inline. If the
   governor set would blow the 3-12 line message budget, split it into its own
   sub-message (footer descriptor: `governors`).
5. **Prediction question — only when non-obvious** (complex operator chains, indirect
   mutations, non-linear execution). Test a *consequence* or *interaction*, not textbook
   knowledge. Skip for straightforward changes (guard, rename, constant).
6. If a prediction was off: name the gap, discuss, resolve before advancing.

**Walk order:** most self-contained first (fewest imports from other changed files),
outward toward integrators and consumers. Comprehension builds from leaves inward.

**Hunk order within a file:** top-to-bottom in source order unless one hunk obviously
depends on a later one — then walk the dependency first.

**Discussion during a walk.** The developer may interrupt at any hunk to explore —
ask for code outlines, cross-references to other files, or explanations of adjacent
symbols. Discussion does NOT advance the footer. Return phrasing when discussion ends:
*"Back to `<file>` hunk K/L — continue, or more to discuss?"*

---

### Checkpoint 3/4: Data Flow, Invariants, and Concerns

**Purpose: trace what the code assumes. Concerns arise naturally here.**

For each data path through a changed symbol:

**Part A — Trace the path:**
1. Input: type, source, shape.
2. Transformations: what happens to the data as it moves through the changed code.
3. Output: type, destination, consumer.

**Part B — Invariants:**
4. What must always be true at this point?
5. New invariants introduced? Prior ones relaxed or removed?
6. Constraints: nullability assumptions, ordering requirements, uniqueness contracts,
   size limits, permission prerequisites.

When type changes are present: show the delta explicitly — old type → new type —
and state what it enables or restricts.

**Part C — Concern (if one exists):**
After naming the invariants, ask: *what does usage assume that the type or code doesn't
actually enforce?* If the answer is something genuinely worth the developer's attention,
surface it. The ⚠️ emoji prefix is required — it makes concerns visually scannable
in long transcripts:

```
> ⚠️ **Concern:** <one sentence — the observation and why it matters>
> `path/to/file.ts:<line>` — flag it, or move on?
```

Do not omit the ⚠️ — every concern must start with `> ⚠️ **Concern:**`.

The developer can:
- **Discuss it** — enter discussion mode
- **Flag it** ("save that") — propose note text, write to Concerns on approval
- **Dismiss it** ("not important, I know") — acknowledge and continue

**One concern per data path.** If multiple things are worth noting, surface the most
important one; offer to collect others at Checkpoint 4.

**Warrants a concern:** type gaps, duplicate definitions, implicit caller contracts,
mutable shared state, silent fallbacks, aggregate-vs-local mismatches — anything where
usage assumes something the code doesn't enforce.

**Does NOT warrant a concern:** style preferences, intentional design choices,
things already named as invariants in Part B, things requiring exhaustive audit.

Ask the developer to predict the invariant or gap only when it is non-obvious — same
criterion as Checkpoint 2. One question per step; resolve before advancing.

---

### Checkpoint 4/4: Discussion and Wrap-up

1. Show the current Progress Tracker — what was covered, what was skipped.
2. If concerns were flagged but not yet written to the notes file, list them briefly
   and offer to capture any the developer wants to keep.
3. Raise one open question the walkthrough surfaced — something worth thinking about,
   not a verdict.
4. Open the floor: "What did you want to think through about these changes?"
5. Discuss freely.
6. Offer to write outstanding items (concerns, planned changes, open questions, discussion
   points) to the notes file. Propose each text; append only after confirmation.
7. Return the notes file path, or offer to create it now if it wasn't created earlier.

---

## Edge Cases

- **Detached HEAD:** use short commit hash for notes filename.
- **No `main` branch:** try `master`; if also absent, ask for base branch.
- **Binary files:** `[binary, skipped]` in overview table, `⏭ skipped` in tracker.
- **Renamed file, no content change:** state as rename in overview, `⏭ skipped` in tracker.
- **File with both staged and unstaged changes:** in `staged`/`unstaged` mode, note that
  the other layer also has changes for that file.
- **No changes in any mode:** state clearly, ask what the developer wanted to review.
- **Notes file write fails:** state, continue the session, offer to retry at the end.

---

## Chaining

- `/walkthrough` — go deeper on a concept surfaced during the walk
- `/review` — escalate a concern to a full severity-rated finding; assess merge readiness
- `/study-card` — document a pattern noticed (if in the study project)
