# Lenses: how to count

Counts are estimates in round numbers. They exist to compare versions of the same diff,
so count every version the same way, and don't argue about a line or two.

## Scenarios

A scenario is a future change request someone could actually file: one sentence, in the
domain's words, like "Customers with 10+ orders get free shipping" or "Partners fetch
the discount through the API". Not a technical task ("refactor the mailer").

Pick the 3 most likely, from these sources, strongest first:

1. **Git history** of the reach: `git log` on the files the diff touches, and the
   cochange output. Kinds of change that already happened several times will happen
   again.
2. **The ticket and requirements:** "later", "phase 2", "for now", options left out,
   follow-up issues.
3. **The domain:** what typically comes next for this kind of feature.

Draw them from different types. Each scenario must touch the diff's reach, and at least
one must cross layers.

| Type | Example |
|---|---|
| Change the rule | the discount threshold depends on the customer's country |
| Add a variant | a second kind of discount, a third export format |
| New entry point | run it from a nightly job, the API, the console, another screen |
| New data through all layers | a new field shown in the form, stored, sent in the mail |
| Remove or switch off | drop the feature for one market |

For each scenario, return: the sentence, its type, and where its likelihood comes from
(a commit range, a ticket line, or "domain").

## Change

For each scenario and version, write the edit list: every place that must change, then
sum it.

- **Units:** count each unit edited or added once. A new file counts as one unit per
  named thing in it that a reader navigates to.
- **Lines of logic:** added plus modified plus deleted. Skip blank lines, comments,
  imports and pure formatting. Count tests separately, under Test.
- **Lockstep edits:** two or more edits that must agree, so that forgetting one breaks
  behavior or leaves the rule inconsistent: a condition repeated in three places, a
  field added in the form but not the serializer. Mark them; a version that removes
  lockstep edits wins even at equal line counts.
- Count edits in existing code too. The reach is in scope.

## Test

1. **List the behavior cases** once, from the requirements and the branches of the rule:
   each distinct input class with its expected outcome (eligible, not eligible, at the
   threshold, no orders). Hostile-input checks and the integration that wires the
   feature up are cases of their own.
2. **For each version and case:** the cheapest level that can verify it, and the lines of
   that test, setup included (records or factories built, mocks, TestBed configuration,
   requests made, assertions).
3. **Levels:**
   - **Unit:** a plain object or function. No database, no HTTP, no framework test bed.
   - **Integration:** a database, an HTTP request, a rendered component with TestBed, a job
     run through the queue.
   - **End-to-end:** a browser or the whole running system.
4. **A healthy shape** has most cases at unit level and one integration test per wiring
   (does the controller call the rule, does the component show its result), not one per
   case. When a version needs integration tests per case, the rule is sitting in the
   layer that the integration test drives.

Report the total lines and the cases per level as `unit/integration/end-to-end`. Setup
lines that grow with each case mean the unit under test asks the caller to know too much.

## Read

Choose one question a colleague would ask about the behavior, like "what discount does
order 42 get, and why?" or "when does this email go out?". Follow the code from the
entry point to the full answer, and count the files you must open. Framework and library
files don't count. Every version uses the same question.

More files is worse even when each file is small. A version that wins Change and Test
but adds files to Read has split something that a reader needs together.
