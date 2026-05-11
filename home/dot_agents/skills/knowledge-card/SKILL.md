---
name: knowledge-card
description: >
  Draft a developer knowledge card in Felix's terse,
  code-first voice for publication on a knowledge-card site. Trigger whenever
  the user asks to "write a knowledge card", "draft a card", "publish this
  as a card", "make a card about X", or invokes /knowledge-card. Also
  trigger when the user explains a Rails, PostgreSQL, Ruby, or general
  programming pattern they say they want to share or document publicly,
  even if they do not say the word "card". The skill produces a generic,
  publishable Markdown draft, copies it to clipboard, and supports
  iterative refinement.
---

# Knowledge Card

Draft a focused, generic, publication-ready developer knowledge card. The publishing site adds the title, license, and author byline. This skill writes the body.

## Workflow

1. Read the underlying code, schema, or docs the card describes. Do not draft from memory or guesses.
2. Verify any factual claim a reader might paste into production. Run tests, read Rails source or guides, confirm version-specific behaviour. When uncertain, say so in the card rather than guessing.
3. Write the draft to `/tmp/<short-kebab-name>.md` using a Bash heredoc (so the Write hook does not trip on substrings like `eval`).
4. Verify zero em dashes: `grep -c '—' /tmp/<short-name>.md` must return 0.
5. Copy to clipboard: `wl-copy < /tmp/<short-name>.md && echo "copied $(wc -c < /tmp/<short-name>.md) bytes"`. Fall back to `xclip -selection clipboard` (X11) or `pbcopy` (macOS) only if `wl-copy` is unavailable.
6. Report the file path and byte count. Do **not** add a recap of what was written. Felix reads the diff in clipboard, not your summary.
7. On follow-up edits, treat any version Felix pastes back as authoritative. Apply only the requested changes. Do **not** re-introduce content he removed.

## Structure

A finished card lands at 3500-4500 bytes after iteration. Typical shape:

- **Intro paragraph** that names the problem in plain prose. No card title (the publishing site adds it).
- **3-5 sections under `##` headings.** Each owns one idea.
- **Compound patterns** are outlined as numbered bold list items, each followed by one explanatory sentence and a complete code block:

  ```markdown
  **1. A unique index on the counter's identity columns.** This is the conflict target.

  ```ruby
  class CreateRequestCounters < ActiveRecord::Migration[8.1]
    ...
  end
  ```
  ```

- **Race conditions or sequencing** are walked through as concrete numbered steps showing what happens at each tick. No abstract paragraphs.
- **Side-by-side comparisons** (before/after, do/don't) use a Markdown table.
- **Code blocks are complete and runnable**: full migration class, full model class with `belongs_to`s, full controller class. Not fragments.
- **End on the why**, not on a summary. The reader leaves with the mental model.

## Writing style

### No em dashes

Replace every `—` with one of: a period that splits the sentence, parentheses for an aside, or a colon. Verify with `grep -c '—' <file>` returning 0.

### No AI filler

Strip these. Rewrite the sentence around them.

| Filler | Replace with |
|---|---|
| "fundamentally" | drop |
| "the foundation of the pattern" | drop |
| "Three pieces fit together:" | "Three pieces:" |
| "Here, an `after_action`" (bridging) | drop "Here," |
| "freshly-committed" | "committed" |
| "The full migration:" announcement | drop |
| "after the index has been consulted" | "after the index lookup" |
| "the read-modify-write window the naive shape relies on does not exist" | "no read-modify-write window remains" |
| "The expression is evaluated server-side" | "Postgres evaluates the expression server-side" |

### Active voice, named actors

Name who does what. "Postgres evaluates" beats "is evaluated". "Rails fires the callback" beats "the callback is fired". Passive obscures the actor and the mental model.

### British spellings

Use `serialise`, `behaviour`, `analyse`, `optimise`. Felix's published cards are consistently British.

### Code first, prose supports

The reader scrolls to the code first. Prose explains *why* each piece matters, not what it says. Default to no comments inside code unless the WHY is non-obvious.

## Generic examples only

Cards must work for any team reading cold. Strip every project-specific identifier. Common substitutions:

| Project-specific | Generic stand-in |
|---|---|
| MonitoringList, Membership, OrgScoped, Vilocify, BillingConsumptionPeriod | Account, Subscription, ApiKey, BillingPeriod, Post, Comment |
| `Current.organization`, `Current.membership` (in card prose) | "the tenant scope", "the per-request user context" |
| company-internal table or column names | generic names that read naturally in Rails |

The actual code being documented may live in a real project. Generalise the *card*, not the underlying code.

## Fundamentals over recipes

A weak card says "do this". A strong card says:

- *Why* a unique index is required (storage-level constraint, conflict target, lock point that serialises concurrent writers).
- *What* `ON CONFLICT DO UPDATE` actually does at the database level (single atomic statement; the INSERT-vs-UPDATE decision happens inside the engine after the index lookup).
- *What* `dependent: :destroy` actually registers (a `before_destroy` callback fired in declaration order, which is why ordering vs `restrict_with_error` matters).

The reader leaves the card with a mental model, not just an incantation.

## Accuracy discipline

- For Rails behaviour claims: run a test, read the source, or cite the Rails Guides verbatim. Do not guess.
- For version-dependent behaviour: name the version cutoff (e.g. "abort propagation through nested `dependent: :destroy` was fixed in Rails 6.1, PR #41602").
- For tests included in a card: run them. Confirm they pass. Do not claim coverage you have not verified.
- When uncertain: say so explicitly in the card text rather than picking a side and hoping.

## Iteration workflow

Felix iterates fast. Expect 3-6 rounds. Common cues:

| Cue | Action |
|---|---|
| "simplify" | Cut prose. Keep code. Merge sections. Drop the section he did not engage with. |
| "more fundamentals-driven" | Add the *why* per piece. Walk through the mechanism step by step. |
| "more example-driven / practical" | Expand fragments to full class wrappers and complete migrations. |
| "remove filler words only agents would use" | Strip everything in the filler table above. |
| "tied to actual usage for X" | Replace generic prose with the specific X scenario as the throughline. |
| "this is my final version" | Save and copy. **No summary, no recap, no commentary.** |
| "copy again" | Re-run `wl-copy`. Nothing else. Do not rewrite. |

## Reference cards

When in doubt about voice, length, or structure, read one of these as a style anchor:

- `/tmp/restrict-deletion-with-multiple-scoped-associations.md` — restricting parent deletion via scoped `has_many` with `dependent: :restrict_with_error`, plus grandparent propagation.
- `/tmp/fixture-helpers-in-rails-console.md` — console-only initializer that exposes test fixture helpers (`users(:alice)`) at the IRB prompt via `TOPLEVEL_BINDING`.
- `/tmp/atomic-counter-with-upsert.md` — concurrency-safe API request counters via `INSERT ... ON CONFLICT DO UPDATE` gated by a unique index.

Read at least one before drafting a new card. They demonstrate the structure, voice, code-first ratio, and length to aim for.

## When this skill is not the right tool

- A long-form tutorial or blog post (cards are short and focused).
- An internal runbook with company-specific names (cards are generic).
- A draft document with conclusion paragraphs, executive summaries, or marketing intros (cards are tight and end on substance).

For those, drop the skill and write freely.
