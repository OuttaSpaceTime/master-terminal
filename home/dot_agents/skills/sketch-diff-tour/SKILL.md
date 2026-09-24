---
name: sketch-diff-tour
description: >-
  Tour a change that does not exist yet. Drafts a proposed change into a throwaway git worktree
  at sketch fidelity, then runs diff-tour over it, so the solution can be read as a narrated HTML
  tour — chapters in a reading order, every hunk beside prose saying what it is for, heat marks on
  the load-bearing decisions — before a single line is committed to the real tree. Lightweight: one
  agent, no fan-out, throwaway code. Use to make a plan concrete enough to judge, to compare two or
  three candidate approaches side by side, or to turn a /sketch or /explore-solutions report into
  something readable. Trigger on "/sketch-diff-tour", "tour this idea", "sketch it and walk me
  through it", "what would this change look like", "show me the diff before you build it",
  "tour the proposed change", "draft this and let me read it". Planning only — the real working
  tree is never touched.
---

# Sketch Diff Tour

`/diff-tour` tours a diff that exists. This skill manufactures the diff first.

The change is drafted into a **throwaway git worktree** off `HEAD`, so `git diff` has something real to
say, and the tour is the ordinary diff-tour page. Nothing lands in the user's working tree. The draft is
scaffolding: it exists to be read, then thrown away.

## Requires diff-tour

This skill drives `diff-tour`'s script. It lives beside this skill:

```
~/.agents/skills/diff-tour/bin/difftour.py
```

If that file is not there, say so in one line and stop. Do not reimplement the tour.

Read `diff-tour`'s `SKILL.md` before narrating — Part 1 (heat, the tour structure) and Part 5 (fragment
shape, hunk placeholders) are the format you write in. Parts 2 to 4 are replaced by this skill's workflow.

## When to use it, and when not

**Use it when** the change is understood well enough to draft but big enough that prose about it is
hard to judge, or when two or three approaches need comparing as code rather than as bullet points.

**Use `/sketch` instead** when a table and a few diff blocks in chat will do. A sketch of two files
does not need a browser page.

**Use `/diff-tour` instead** when the code already exists.

**Use `/code-review` instead** when the question is "is this correct", not "is this the right shape".
This skill verifies nothing.

## Workflow

### 1. Pin down what is being drafted

If a `/sketch` or `/explore-solutions` report exists for this change, read it and take the file list and
the decisions from there. Otherwise get the requirement from the user in one exchange.

Only one thing must be settled before drafting: **which approach**. If two or three are live and the
user has not chosen, draft them all — see *Competing approaches* below — rather than picking silently.

### 2. Read every file you will touch

No exceptions. A draft written against remembered code produces a tour of imaginary hunks, which is
worse than no tour. Match the existing names, imports, indentation and idiom exactly.

### 3. Open the worktree

From the repository root:

```
BASE=$(mktemp -d -t sketch-tour-XXXXXX) && git worktree add --detach "$BASE/tree" HEAD && echo "$BASE"
```

The tour is written to `$BASE/`, one level above the worktree, so it outlives the worktree's removal.

The worktree starts at `HEAD`, so uncommitted work in the real tree is **not** in it. If the sketch
builds on uncommitted work, seed it and make it the baseline before drafting, so the tour shows only
the sketch:

```
git diff HEAD | git -C "$BASE/tree" apply && git -C "$BASE/tree" commit -aqm baseline
```

### 4. Draft at sketch fidelity

Write the change into `$BASE/tree`. Sketch fidelity means the **shape is real and the filling may not be**:

- Call sites, signatures, wiring, migrations, routes, config: real, exactly as they would be written.
- Bodies whose content is obvious or mechanical: a one-line stand-in and a `TODO` naming what goes there.
- Anything guessed: write the guess, then mark it `fishy` in the tour. A guess left out of the draft
  cannot be argued with; a guess in the draft can.

Tests are part of the shape. Draft the test names and their assertions even where the bodies are stubs —
the tests are usually the clearest statement of what the change means.

Do not run the tests. Nothing here is meant to pass.

### 5. Tour it

From inside `$BASE/tree`:

```
~/.agents/skills/diff-tour/bin/difftour.py --setup dirty
```

It prints `WORK=`, `ARGS=`, `DIFF=` and twelve empty topic folders. There is no `ASK:` line for a
working-tree target, so nothing to confirm.

Read `$WORK/diff.txt` with the Read tool. Then, **as a single agent, no fan-out** — a sketch is small
and forking costs more than it saves:

1. Cluster the hunks into topics by reason, in a reading order where each topic relies only on what
   came before. A sketch usually has two to five. Follow *On finding topics* and *Reading order* in
   diff-tour's Part 2.
2. Write `$WORK/00-intro.html`: an `<h1>` and a short summary. For a sketch the summary
   answers three things — what problem this solves, what the approach is, and what it costs (the
   migration, the new dependency, the behaviour that changes for everyone).
3. Write one `$WORK/topic-NN/fragment.html` per topic, in the shape given in diff-tour's Part 5.
4. Assemble, pasting `ARGS=` verbatim, with the output **outside** the worktree:

```
~/.agents/skills/diff-tour/bin/difftour.py --assemble "$BASE/sketch-tour.html" <ARGS> ++ "$WORK"
```

### 6. Hand over

Two or three lines, the `file://` URL last and alone:

```
<the open decisions, one line each, only if there are any>
Say the word and I will open it in your browser.
file:///tmp/sketch-tour.Ab3xY9/sketch-tour.html
```

Do not summarise the tour in chat; the page does that better. Do not open it unasked.

### 7. Dispose

Ask what happens to the draft, once, after handing over the URL:

- **Throw it away** — `git worktree remove --force "$BASE/tree"`. The tour HTML survives; it is
  self-contained.
- **Keep it** — leave the worktree and say where it is, so the user can `cd` in and keep drafting.
- **Promote it** — copy the drafted files into the real tree. Only on an explicit yes, and only then
  is this no longer planning.

Never promote a draft on your own initiative.

## Heat means something different here

diff-tour's heat asks *how carefully should this be read*. On a sketch, nothing has been verified into
existence yet, so heat asks **where is this change actually being decided**. Same five levels, same
placeholder syntax, re-aimed:

| Level | On a sketch |
|---|---|
| `skip` | mechanical fallout — the import, the route line, the renamed call site |
| (none) | ordinary shape, follows from the approach |
| `note` | a decision the user must knowingly accept: a default, a name that will be hard to change, a dropped case |
| `fishy` | a guess. Where the draft asserts something about existing code or an external contract that was not confirmed |
| `hot` | the load-bearing choice. Get this wrong and the whole approach is wrong, or it is expensive to undo later: the data model, the migration, the boundary, the thing everything else is built on |

`fishy` is the level that earns this skill. Every place the draft guessed gets one, with the guess named
in the reason. A tour with no `fishy` on a change nobody has built yet is a tour that is hiding something.

`hot` is scarce. One or two per tour, on the choices that are cheap now and expensive after
implementation.

## Competing approaches

Two or three candidates get one worktree and one tour each: repeat steps 3 to 5 per approach, each with
its own `BASE`. Say which approach a tour is in its `<h1>` and in the first sentence of the summary.

Hand over all the URLs together, with one line per approach naming the trade-off that separates it from
the others. Do not declare a winner in chat — the tours are the argument, and the choice is the user's.

Stop at three. Beyond that, narrow with `/explore-solutions` first.

## Rules

<critical>
**The real working tree is never touched.** All drafting happens inside the worktree. No file outside
`$BASE` is created or edited, and nothing is committed to the user's branch.
</critical>

- **No fabricated context.** Every line of the draft is written against a file read in this session.
- **Nothing is verified.** No tests are run, no claims of correctness are made. Judgement is the user's.
- **The draft is disposable.** Never let effort spent drafting become an argument for keeping it.
- **One agent.** No fan-out. If the change is large enough to need workers, it is too large to sketch —
  say so and suggest building it and touring the result with `/diff-tour`.
