---
name: local-review-check
description: Audit your own code-review coverage of a branch or MR using local-review.nvim comments — report which diff hunks you have not commented on yet, and judge honestly whether your comments show real understanding of the change or just restate it. Use this whenever the user asks "did I comment every hunk", "which hunks did I miss", "do I understand this MR well enough", "am I ready to approve/merge this", "check my review coverage", "have I reviewed all of this", or invokes /local-review-check — and also when they have been leaving local-review.nvim comments on a branch and want to know whether they are done reviewing. Reads comments non-destructively; never clears them.
---

# Local Review Check

The user reviews code by leaving `local-review.nvim` comments on lines as they read a
branch. This skill answers two questions about that pass:

1. **What have I not looked at?** — which hunks of the diff carry no comment.
2. **Do I actually understand this?** — whether the comments they did leave show
   comprehension, or just narrate what the diff already says.

The second question is the one that matters and the one they cannot answer alone. A
reviewer who has commented every hunk can still have understood nothing; a reviewer with
four comments on the four load-bearing hunks may understand the change completely. Count
hunks, but judge on content.

## Never clear the comments

The user is mid-review. Their comments are the work product. `LocalReviewExport` and
`LocalReviewGh` delete comments after reading them — never invoke those. The bundled
reader uses the plugin's read-only path.

## Workflow

Run both scripts from the repository root. They are siblings in this skill's `scripts/`.

```sh
scripts/read_comments.sh > /tmp/lrc-comments.json
scripts/review_coverage.py --comments /tmp/lrc-comments.json --json /tmp/lrc-coverage.json
```

`read_comments.sh` emits every comment as JSON (`path`, `line`, `line_end`, `body`,
`stale`). It loads the plugin explicitly rather than relying on
`+LocalReviewExportPreserve`, because that command is not registered in a headless run
when the config lazy-loads the plugin on a UI event.

`review_coverage.py` maps each comment onto the hunks of `git diff <merge-base>` and
prints a per-file table. Useful flags:

- `--base <ref>` when the branch is not cut from `main`/`master`
- `--max-gaps 0` to list every uncommented hunk rather than the first six per file
- `--generated <glob>` (repeatable) to re-bucket derived files for this repo

Read `/tmp/lrc-coverage.json` for the hunk diffs themselves — you need the actual changed
lines to judge whether an uncommented hunk mattered, and to judge whether a comment
engages with its hunk.

### Why the diff is against the working tree

Comment anchors are line numbers in the files as they sit on disk right now. The script
therefore diffs `<base>` against the working tree, not `<base>...HEAD`. Diffing against
HEAD would shift every line number by whatever is uncommitted and silently attribute
comments to the wrong hunks. If you ever compute hunks yourself, preserve this.

## Bucketing: not every hunk deserves a comment

The script splits hunks into `source`, `test`, and `generated`, and reports each
separately. This is not cosmetic. A Rails branch that adds a NOT NULL constraint might
touch 25 fixture hunks and 9 `schema.rb` hunks — real changes, but regenerated ones that a
reviewer reads in bulk and confirms in aggregate. Counting them flat produces "13/105
commented", which reads as a failing grade for a review that may in fact be thorough where
it counts.

So: report the buckets, and lead with `source`. Treat an uncommented `schema.rb` hunk as
unremarkable and an uncommented backfill migration as a real gap. Say which uncommented
hunks you think genuinely need the user's eyes and which they can wave through — that
judgment is the value you add over the raw count.

## Judging understanding

Read each comment against the hunk it sits on. You are looking for the difference between
narration and comprehension:

**Narration** restates the line. "from nil to ''", "normalizes to Infinity", "added a
scope". The comment would be identical if the reviewer had understood nothing about why
the change exists. These are not worthless — they are how people read — but a review made
entirely of them has not yet engaged with the change.

**Comprehension** names something not visible in the line itself: why this approach over
the obvious alternative, what breaks without it, what it costs elsewhere, which other hunk
it depends on. A comment like "EOL date depends on eol_reached, so `normalizes` can't do
it — it has no access to the other attributes" shows the reviewer traced the constraint.

Then look at the *shape* of the coverage, which is more telling than the ratio:

- Are the commented hunks the consequential ones? A review that comments every model file
  and skips all twelve migrations has inverted the risk.
- Do the comments connect hunks to each other? A change usually has a few places that must
  agree. A reviewer who has noticed that has understood the change; one commenting each
  file in isolation may not have.
- What did they leave as open questions? `TODO:`/`why…?` comments are the honest signal of
  where their own understanding is thin. Surface them — do not quietly answer them and
  present the review as complete.
- Do any comments contradict the code, or each other? That is the strongest evidence of a
  real misunderstanding, and worth more than any coverage number.

Be straight with the user. If the review is thin, say so and say where. A reassuring
summary of a shallow review is the one outcome that actively costs them something — they
will merge on the strength of it.

## Report structure

```
## Coverage
<the bucket table, then the uncommented hunks that you think actually need attention,
 with one line each on why — not a dump of the script output>

## What your comments show
<what the comments demonstrate they understood, concretely, citing comments>

## Where understanding looks thin
<hunks whose logic no comment engages with; contradictions; the reviewer's own open
 questions, quoted>

## Verdict
<one paragraph: ready to approve, or the specific things to read before deciding>
```

Quote comments verbatim when you cite them, so the user recognises their own words.

## Follow-ups

The natural next step is usually answering the open questions the review surfaced. Offer
that, and offer to re-run the check after the user adds more comments. Ask before clearing
anything — and if they do want their comments cleared, that is
`nvim --headless '+LocalReviewClear' +qa`, run only on explicit request.
