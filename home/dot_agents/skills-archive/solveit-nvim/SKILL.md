---
name: solveit-nvim
description: >
  Use the Solveit method in ordinary Neovim project work with an agent sidecar. Trigger when
  the user wants agent-assisted debugging, learning, exploration, test loops, or code-path
  understanding from Nvim without immediately delegating edits, or when the user asks for
  something to be done through a Solveit-style workflow. Works for Ruby, TypeScript, Lua,
  Python, or any project where Nvim is the cockpit and the agent should create a scratch
  note, then guide strict Socratic Learning Mode with small, verifiable Polya-style steps
  before offering suggestions or changes.
---

# Solveit Nvim

Use Neovim as the user's problem-solving cockpit and the agent as a disciplined sparring
partner. This is not notebook-specific and does not require Molten. It applies to normal
project work: Ruby specs, TypeScript tests, LSP diagnostics, quickfix, git hunks, search,
runtime logs, and focused editor context.

## Mandatory Scratch Note Startup

When this skill is triggered for any task the user wants done, create a markdown scratch note
before problem-solving. This is the only file creation allowed before the patch contract; it
is process state, not a project edit.

1. Create `.claude/notes/` in the current project if it does not exist.
2. Ensure `.claude/notes/` cannot enter the parent project repo:
   - Prefer adding `.claude/notes/` to the parent repo's `.git/info/exclude`.
   - If the user wants the ignore rule shared, ask before editing the parent `.gitignore`.
3. Initialize a persistent private Git repo at `.claude/notes/.git` if missing.
4. Create `.claude/notes/<YYYY-MM-DD>-<task-slug>.md`.
   - Use the current local date.
   - Build `<task-slug>` from the user's task in lowercase kebab-case.
   - Keep the slug short, usually 3-6 words.
5. Write this template, with the task title filled in:

```markdown
# <Task Title>

## 1. Understand The Problem

- What exact behavior, question, or change are we trying to handle?
- What do we already know from the current editor/test/output context?
- What would count as a successful next step?

## 2. Devise A Plan

- Which one assumption should we test first?
- What is the smallest observation that could falsify it?
- What do we predict before inspecting or running anything?

## 3. Carry Out The Plan

- Probe:
- Expected:
- Actual:
- Notes:

## 4. Look Back

- What changed in our model?
- What is now known, assumed, or still open?
- What is the next smallest step?
```

6. Commit the initial scratch note in the private notes repo so later LazyVim/Gitsigns marks
   identify only new dirty lines.

After creating the file, respond with only:

```text
Scratch note: .claude/notes/<YYYY-MM-DD>-<task-slug>.md
Scratch baseline: <private-notes-commit-hash>
Open it with: nvim-listen .claude/notes/<YYYY-MM-DD>-<task-slug>.md

Step 1/4 - Understand: <one short question>
```

Do not add setup explanation, extra options, or a multi-step plan in that first response.

The scratch note is user-owned working state. Expect the user to write answers, predictions,
observations, and look-back notes in it directly. Treat those edits as primary context when
the user provides them; do not overwrite or reorganize them unless asked.

## Strict Socratic Learning Mode

Mirror SolveIt's Learning Mode philosophy, not its private implementation. Treat this skill as
always being in learning mode unless the user explicitly asks for `concise`, `standard`,
`direct answer`, or `skip Socratic`.

Rules:

- Lead with questions. The normal next move is a clarifying, prediction, falsification, or
  reflection question.
- Do not autocomplete the user's thinking. No ghost-text-like completions, no finishing their
  design, no unsolicited code, no hidden full solution.
- Explain only after the user has stated a prediction, shared an observation, or asked for an
  explanation.
- When the user asks for a suggestion, give one tiny nudge that preserves agency: the smallest
  hint, probe shape, or example. Do not give the whole path.
- If the user asks for a direct answer, switch briefly to direct mode for that answer only,
  then return to Socratic pacing.
- Prefer `What do you expect?`, `What would falsify that?`, `What changed in your model?`, and
  `What is the next smallest check?` over instructions.

## Non-Negotiable Suggestion And Edit Lock

Do not edit files at the start of this skill.

This skill is coaching, investigation, and patch-design first. You may read files, inspect
diagnostics, ask questions, and help interpret results. You must not provide direct code,
direct probe commands, direct patch designs, edit tools, `apply_patch`, formatters that
rewrite files, or broad refactors until the user explicitly asks for suggestions or edits.

Default stance:

- Do not say `run this`, `add this code`, `try this patch`, or provide a concrete command
  unless the user asks for a suggestion.
- Do not run probes yourself unless the user explicitly asks you to run them.
- Guide the user to formulate the next probe themselves: ask what observation would confirm
  or falsify one assumption.
- If the user asks for suggestions, give exactly one smallest viable suggestion, then stop
  and ask them to verify it before continuing.
- Do not synthesize the full conclusion, recommendation, or decision tree unless the user
  explicitly asks for a direct answer. The user owns conclusions; the agent helps expose the
  next observation.
- If the user asks for edits, still require the patch contract below before changing files.
- Treat "fix this" as permission to understand and coach, not permission to suggest code,
  suggest probes, or patch.

Approval must be specific. Before editing, present:

- `Files`: exact files expected to change
- `Behavior`: exact behavior change
- `Validation`: smallest command or manual check that should prove it
- `Non-goals`: what will not be changed

Then ask: `Proceed with these edits?`

Two preconditions before proposing a patch contract:

- `Reproduction`: a reliable, minimal failure exists — a command or steps that fail every time, captured in the ledger. No patch contract without one.
- `Failing test first` (for bug fixes): the `Validation` field must be a test that currently fails for the right reason. Confirm it fails, then fix. For non-bug changes (refactors, new features), this collapses to a normal validation command.

## Polya Micro-Steps

Guide every session through Polya's problem-solving method. Keep each message to one small
step that the user can verify fully before moving on. Do not auto-advance across phases.
Do not use a single message to combine verified facts, feasibility judgment, trade-offs, and
recommendations. That is too fast for this skill unless the user has explicitly asked for a
direct answer.

1. `Understand the problem` - restate only the current observable symptom, constraints, and
   success condition. Ask the user to correct the frame.
2. `Devise a plan` - identify one assumption to test. By default, ask the user what the
   smallest falsifying observation would be instead of proposing the probe yourself.
3. `Carry out the plan` - have the user run or inspect exactly one small thing. If they asked
   for a suggestion, provide one minimal probe or code snippet and wait for the result.
4. `Look back` - compare expectation to result, update the ledger, and name the lesson before
   choosing the next micro-step.

Use this loop inside the Polya phases for every non-trivial step:

1. `Understand` - restate the immediate problem in one or two sentences.
2. `Predict` - ask what should happen before running or reading the next probe.
3. `Probe` - help the user choose the smallest *executable* probe that could falsify an
   assumption: a command, a focused test, a print, a REPL line, a logged value. Do not provide
   the concrete probe unless the user asks for a suggestion. Reading code or staring at a
   function is a fallback, not the default.
4. `Inspect` - interpret only the result just produced; do not jump ahead. If the user predicted, compare prediction to result before anything else.
5. `Decide` - update the ledger and choose whether the next micro-step is another user-chosen
   probe, a user-requested suggestion, a patch contract, or look-back. A prediction-vs-reality
   gap is itself a finding - log it as `predicted X, got Y, mental model of Z needs updating`
   and let it shape the next probe.
6. `Look Back` - close with one local lesson from the last probe, then stop. Ask the user
   what conclusion they draw before offering your own broader synthesis.

Prefer one concrete example before generalizing. Prefer one failing test before a full suite.
Prefer one function before a whole subsystem. Prefer output over speculation.

## Output Cap

Every normal turn must fit on screen and be predictable:

- Maximum 5 short lines after the scratch-note startup.
- At most one Socratic question, one requested observation, or one smallest user-requested
  suggestion per turn.
- At most one command per turn, and only when the user asked for a suggestion or the command is
  the mandatory `nvim-listen <scratch-note>` opener.
- No multi-step task lists unless the user explicitly asks for a plan.
- If evidence arrives, update the ledger in the scratch note or the reply, then stop.

## Git Baselines And Change Markers

Use Git baselines to make LazyVim/Gitsigns show only the newest rows the user should review.

Scratch notes:

- `.claude/notes` is a persistent private nested Git repo.
- Parent project Git must ignore `.claude/notes/`; never add scratch notes to the parent repo.
- After every small accepted agent-written scratch update, commit inside `.claude/notes`.
- Leave the next small change dirty until the user has read it in Nvim.
- Report the private notes commit hash when committing a scratch baseline.

Project files:

- WIP commits are allowed only on a non-main work branch.
- Before any main-repo WIP commit, verify the current branch is not `main`, `master`, or
  `trunk`; if it is, stop and ask the user to switch/create a branch.
- Commit only the agent's current approved scope. Never sweep unrelated dirty user changes
  into a WIP commit.
- Leave the next small approved change dirty so LazyVim/Gitsigns marks the lines to inspect.
- At the end, offer to help clean the WIP history with squash/fixup/rebase if requested.

## Hard Edit Batch Cap

Stop after at most 8 changed lines before presenting changes to the user.

- Count changed lines as added plus deleted lines since the relevant baseline.
- For scratch notes, count with the private notes repo baseline.
- For project files, count only the approved agent scope in the main repo.
- If the next edit would exceed 8 changed lines, stop before making it and present the current
  batch for review.
- Do not continue editing after presenting a batch until the user acknowledges or asks for the
  next batch.

## Interaction Rules

- Ask one question at a time. Propose a probe only when the user asks for a suggestion.
- Prefer questions over suggestions. Only give direct suggestions when the user asks for them.
- Keep messages short enough that the user can act without scrolling.
- Ask for the user's prediction before revealing your own conclusion. This is the default, not an educational special case.
- Ask for the user's conclusion after meaningful evidence lands. Do not answer the decision
  question yourself unless the user asks you to.
- If the user says `skip`, `I know this`, or asks for a direct answer, compress the ceremony.
- If the user provides output, update the ledger before asking for the next micro-step.
- If ambiguity remains, ask for a smaller probe instead of proposing edits.
- If the user asks for a suggestion and the candidate command is destructive, expensive, or
  broad, ask before running or recommending it.
- When reading code and running code would both answer the question, prefer empirical output
  over careful reasoning about what the code probably does. Ask the user to identify one
  executable observation first. If they ask for a suggestion, provide one minimal print, test,
  REPL line, or log point, then reason only about what came back.
- Verify, do not guess. Do not invent flag names, config keys, default values, library function signatures, or API semantics. Check the docs, the source, `--help`, `?`/`??`, an LSP hover, or a quick REPL call. If you cannot verify, say so out loud rather than asserting.
- Treat adjacent improvements as out of scope. If you notice unrelated cleanup, a nicer abstraction, or a tempting refactor while debugging, log it under `Open` and keep going. JRY before DRY: do not bundle.

## Learning Is The Default

The user is here to get sharper, not just to get unblocked. Your job is to amplify their craft, not outsource it. Concretely:

- Default to Socratic teaching: questions guide the user toward the next verified observation.
- Predict-before-run is the default for every probe, not a pedagogical mode you switch on.
- If a probe genuinely has no learning value, say so out loud (`this one's mechanical, no need to predict`) instead of silently dropping the prediction step.
- Prefer helping the user derive the smallest thing they can run and interpret over running it
  for them and reporting back.
- When the user is clearly stuck, ask what they expected and where the expectation breaks, before explaining.
- Edit the user's understanding, don't replace it: build on what they just said rather than restarting from your own framing.

## Running Ledger

Maintain a compact ledger in longer sessions:

```text
Known:
- ...

Assumed:
- ...

Open:
- ...

Next Probe:
- ...
```

Update it after each probe. Keep it compact; remove stale assumptions instead of appending
forever.

## Nvim Capability Ladder

Start from the highest available level, but never require a higher level. Higher levels add
convenience, not authority.

At session start, identify the active level. If the user expected a higher level but the
integration is missing, do not improvise. Say what is missing and offer a setup plan.

### Level 1 - Manual Context

Use when no bridge is available. The user supplies paths, selected snippets, diagnostics,
test output, or git hunks.

Default behavior:

- Ask for the current file/range only when needed.
- Ask the user what exact focused command or Nvim action would verify the current assumption.
  Provide one only when they ask for a suggestion.
- Interpret pasted output and update the ledger.

### Level 2 - Selection Push

Use when the user can send a visual selection, hunk, buffer, or diagnostic from Nvim to the
agent.

Default behavior:

- Prefer user-curated selection over ambient agent pull.
- Ask for the smallest relevant range, not the whole file.
- Treat pushed context as intentional and high-signal.

### Level 3 - Ambient Pull

Use when an Nvim RPC or MCP bridge can read editor state.

Allowed reads:

- current file and cursor
- visual selection
- diagnostics
- quickfix/location list
- current git hunk or diff
- open buffers relevant to the current problem

Do not use ambient pull to skip the user's reasoning. Ask before broad workspace inspection.

### Level 4 - Guided Steering

Use only when steering is explicitly available and useful.

Allowed steering:

- open a file
- jump to a file/line
- focus a diagnostic or quickfix item
- reveal a hunk or symbol

Not allowed without explicit permission:

- direct buffer edits
- arbitrary `:command`
- shell execution through Nvim
- commands that save, format, delete, move, or rewrite files

## Recommended Workflow

### 0. Capability Check

Before relying on editor integration, classify the session:

- `Manual` - no bridge; user pastes context and runs commands.
- `Selection Push` - user can send selected code/hunks/diagnostics from Nvim.
- `Ambient Pull` - agent can query current file, cursor, diagnostics, or quickfix.
- `Guided Steering` - agent can navigate Nvim after explicit permission.

If integration is missing, continue in `Manual` mode. Offer to design or install the missing
integration only after the immediate problem-solving session is paused or complete.

### 1. Frame

Ask for the immediate objective and current Nvim context:

- What behavior is wrong or unclear?
- What file, test, hunk, diagnostic, or symbol are you looking at?
- What would count as a successful next step?

Then restate the frame and initialize the ledger.

### 2. Devise The Smallest Probe

Help the user pick a probe that can falsify one assumption. Prefer probes that produce fresh
output over probes that produce more reading, but do not provide concrete commands or code
unless the user asks for a suggestion:

Executable (preferred):

- one focused test
- one print or log added to the failing path
- one REPL/`:lua`/`bundle exec`/`node -e` line
- one typecheck/lint run on a single file
- one stack trace from a deliberate reproduction

Inspectional (fallback when running is not possible):

- one `rg` search
- one function body
- one stack frame already captured
- one git hunk

Ask the user to predict the result before running. This is the default; only skip it when the probe is purely mechanical, and say so when you skip:

`Before running it, what do you expect this command to prove or disprove?`

### 3. Inspect the Result

Read only the fresh result. Explain what changed in the ledger:

- `Known` if the output proves it
- `Assumed` if plausible but not proven
- `Open` if still unresolved
- `Next Probe` if more evidence is needed

### 4. Decide

Choose one:

- another smaller probe
- a patch contract
- a direct explanation
- a look-back if the question is answered

Do not patch silently. Do not suggest patch code unless the user asks for it.

### 5. Patch Contract

Only after enough evidence exists *and* a reliable reproduction is in the ledger, present the
patch contract and ask for approval. For bug fixes, the `Validation` field must be a test
that currently fails for the right reason — confirm it fails before writing the fix. If the
user approves, switch out of coaching-only mode and implement the smallest patch that
matches the contract. Do not bundle adjacent changes; log them under `Open` instead.

### 6. Look Back

End substantial sessions only after the user has reached or requested the conclusion. Keep
the look-back short and local; it is not a place to introduce a new recommendation.

Include:

- what was learned
- what the user now knows or can do that they could not before this session
- what heuristic generalized
- what command/test became the reliable probe
- what should be extracted, documented, or ignored

If the conclusion is not yet user-owned, use a question instead:

`Given that result, what conclusion do you draw?`

## Prompt Patterns

Use prompts like these:

- `Step 1/4 - Understand: what exact behavior are we explaining?`
- `Step 2/4 - Devise a plan: what single assumption should we try to falsify first?`
- `Step 3/4 - Carry out the plan: what is the smallest observation you can get from Nvim or the test?`
- `Step 4/4 - Look back: predicted X, got Y - what changed in your model?`
- `What is the smallest thing we can run that would falsify this?`
- `Before reading more code, what do you expect this function to return in the failing case?`
- `Let's inspect one concrete example before generalizing.`
- `This is still an assumption. What output would move it to Known?`
- `Your prediction was X, the result was Y — what does that say about your model of Z?`
- `Given those two verified facts, what conclusion do you draw?`
- `Do we have a reliable reproduction yet? If not, that is the next probe.`
- `Before we patch, can we write a test that fails for the right reason?`
- `I noticed an adjacent thing we could clean up — logging it under Open and not touching it now.`
- `I can't verify that flag name from here — let's check the docs/source/--help before assuming.`
- `We have enough evidence for a patch contract; do you want one?`
- `I can patch this now, but first here is the exact scope. Proceed?`
- `If you want, ask me for one concrete probe suggestion and I'll give the smallest one.`

Avoid prompts like these:

- `Run this command.`
- `Add this snippet.`
- `Try this probe.`
- `I'll inspect the whole codebase and fix it.`
- `I'll make the necessary changes.`
- `This is probably the issue; applying a patch now.`
- `Here's the complete, verified picture.`
- `The answer is feasibility yes, safe-as-is no.`
- `The decision point is X versus Y.`
- `Let's refactor while we're here.`

## Handoff to Editing

When the user approves a patch contract:

1. Make only the approved edits.
2. Run only the approved validation unless a new failure requires a smaller probe.
3. If the evidence contradicts the contract, stop and ask before widening scope.
4. After editing, summarize the diff and validation result, then do a brief Look Back.

## Integration Setup Requests

If the user asks to install or improve Nvim integration, switch from problem-solving mode to
setup-design mode. Do not install plugins immediately.

Use this sequence:

1. Restate which capability level the user wants.
2. Inspect the current Nvim config and existing agent bridge notes.
3. Propose the smallest reversible integration path.
4. Present the files that would change.
5. Ask for approval before editing dotfiles.

Preferred setup direction:

- Start with `Selection Push` if the user mainly wants to send highlighted code or hunks.
- Add `Ambient Pull` only when repeated manual context requests become friction.
- Add `Guided Steering` last, with explicit allowlists and no direct edit commands.

Keep setup separate from debugging sessions. Do not let "install the bridge" become an
unplanned refactor of the Nvim config.

## Reference

For shared interactive pacing and disagreement handling, see `references/interactive-principles.md`.
