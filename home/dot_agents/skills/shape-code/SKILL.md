---
name: shape-code
description: >-
  Measures whether a working change is shaped well for what comes next, with counts
  instead of opinions. Writes three likely future feature requests, then counts for the
  change as written and for alternative designs: the units and lines each request would
  touch, the test lines and test levels needed to cover the behavior, and the files a
  reader opens to understand it. Applies the alternative that clearly wins, brings bigger
  or riskier ones to the human, and states design principles only as predictions the
  counts confirm or refute. Use after implementing a change that works, when asking
  whether code is in the right place (MVC layer, model vs controller vs service, how to
  split a component), whether a design pattern pays off, how to make code easier to test,
  or to train one's own design judgement on real diffs.
argument-hint: "[base ref or commit range]"
---

# Shape code

Agents write code that works, and a reader checks it for correctness. Whether everything
is in the right place rarely gets asked, and asked as "is X better than Z?" it has no
answer anyone can check. This skill asks a question that does: **what will the next
changes cost, in this design and in its alternatives?** It counts, and the counts decide.
Principles and patterns come last, as predictions the counts confirm or refute for this
code. A principle is never a reason on its own.

The report is the product. It is a matrix and one line per decision, scannable in a few
seconds, with every line something the human can act on. A long or overwhelming report
is a failed run, however good the analysis behind it.

## Terms

- **The diff** is the change being shaped: a commit range or uncommitted work, as it was
  before this skill began.
- **Existing code** is every line the diff neither adds nor modifies.
- **Existing churn** is the lines of existing code a version modifies, moves or deletes,
  renames and updated call sites included. Code a version writes inside the diff doesn't
  count.
- **Intended behavior** is what the requirements, specifications or docs ask for, what
  tests pin down, and what code in this codebase relies on. A detail nobody could sensibly
  rely on (key order, whitespace, a typo in a message) doesn't count.
- **A unit** is anything with a name a reader navigates to: a method, function, class,
  module, component, template or config entry. A scenario touching a unit counts it once,
  however many of its lines change.
- **A version** is a design of the diff. **V0** is the diff as written. V1, V2, … are
  alternatives.
- **A scenario** is a concrete future change request, S1–S3.
- **The reach** of the diff is the diff plus what it plugs into: its callers, the rules
  and structures it extends, and the files git history shows changing with it. Analysis
  and counts cover the reach, not only the diff's lines: a small change often costs
  through where it lands.
- **An area** is a part of the diff that can be judged on its own, like a rule and its
  consumers, or a screen. Most diffs are one area.
- **Sensitive code** is code where a small mistake is expensive. You judge it yourself;
  see Sensitive code below.

## The three lenses

Each lens is a count. The sub-agents count by [references/lenses.md](references/lenses.md).

1. **Change.** For each scenario: the units touched, the lines of logic changed, and the
   lockstep edits (edits that break something when one of them is forgotten).
2. **Test.** The behavior cases the diff must cover, listed once. For each version: the
   cheapest test level that verifies each case, and the lines of setup and assertion it
   needs. Good isolation moves cases down the test pyramid and needs fewer lines.
3. **Read.** For one concrete question about the behavior ("what discount does order 42
   get?"): the files a reader opens to answer it. Change and Test reward extracting more
   units; Read is the counterweight against a maze of tiny ones.

**A version beats V0** when it is better on Change by at least 2 units or about 30% of
the lines summed over the scenarios, or better on Test by about 30% of the lines, and no
worse on any lens beyond noise. One more file on Read, or one more lockstep edit, is
worse. Smaller differences are ties: estimates are rough, and a tie is reported as one.

**Counts can be gamed.** Shorter but denser doesn't count: several statements packed
into a line, long call chains, clever tricks, metaprogramming where two plain cases would
do. Every concept a version adds (a class, an object, a flag or mode an abstraction
branches on, a pattern) is listed next to its counts.

## Three lists

Every version ends on one list.

- ✅ **Apply.** It wins. It keeps the intended behavior, verifiably. It touches existing
  code only where the diff needs it, and then states why in one sentence ("the diff
  needed X because existing code does, lacks or is shaped as Y"), with existing churn at
  most about twice the lines it saves. It touches no sensitive code, and the measured
  check in step 5 confirmed the win. Applied without asking.
- 🛠️ **Your call.** It is worth it, but not safe to apply unasked: it changes intended
  behavior, reaches further into existing code, touches sensitive code, adds a dependency
  or a schema change, introduces a way of doing things this repo doesn't use yet, or wins
  some scenarios and loses others. Changes like these are welcome here when the counts
  make them well worth it. Each one states its win, its cost, its risk and your
  recommendation.
- 🚫 **Not pursued.** No win beyond noise, worse on a lens, a prediction that failed,
  evidence that didn't hold, or it contradicts a decision. One line each.

## Sensitive code

Sensitive code never goes on Apply, however small the edit: small edits in sensitive code
are where review pain comes from. Judge it from these signals. One strong signal is
enough; the report names it.

- **Money and access:** payments, prices, invoices, balances; authentication, sessions,
  permissions, authorization checks; tokens and secrets.
- **Persistent data:** writes to the database, migrations, background jobs that change
  records, imports and exports, deletion.
- **Contracts:** public API endpoints and response shapes, webhooks, events other systems
  consume, URLs people bookmark, file formats.
- **Input from outside:** validation, sanitizing, limits on what a client may send.
- **Concurrency:** locks, transactions, retries, caching and its invalidation.
- **History:** a hot spot in the cochange output (many commits, many partners), or code
  with a history of bug-fix commits (`git log --grep` for fix, bug or revert on the file).
- **No safety net:** code no test covers.
- **The code says so:** comments warning about it, or unusual care like extra logging,
  defensive checks or feature flags.

## Steps

Track these steps in your todo list, so that verification and cleanup don't get skipped:

```
- [ ] 1. Scope: the diff, the reach, sensitive code, cochange output
- [ ] 2. Scenarios written, then confirmed by the human
- [ ] 3. Versions counted by both passes
- [ ] 4. Counts verified, predictions checked, versions sorted
- [ ] 5. Apply versions measured, applied, cleaned up, tests passing
- [ ] 6. Report
- [ ] 7. Your call versions applied as the human approves them
```

### 1. Scope

- **The diff:** the base or commit range the human named, if any. Otherwise uncommitted
  work against `HEAD`, and if there is none, the branch against its merge-base with the
  default branch. If the diff is empty, say so and stop.
- **Trivial diffs stop here** with one line, like `Nothing to shape: rename only.`
  Trivial means a typo, a config value, a pure rename, or only tests or docs. Size alone
  is never a reason to stop.
- From the repository root, run `<skill dir>/scripts/cochange.py <base>`, where
  `<skill dir>` is this skill's base directory and `<base>` the diff's base or range. It
  prints the hot spots and the files that change together with the diff's files.
- Read the project's written rules: `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`,
  `REVIEW.md`, `docs/adr/`, architecture docs. Decisions recorded there are settled. A
  version that contradicts one goes to Your call only when its counts show a real cost,
  naming the decision.
- Map the reach, and mark the sensitive code in it.
- **Areas:** most diffs are one area. Split a large diff into at most 3 areas, the ones
  with the most units and the hottest files. Name the rest in the report as not shaped.
- **The brief** for every sub-agent: the requirements in the human's or the ticket's own
  words; decisions already made (what, not why); questions the human asked, quoted; the
  diff command; the reach; the cochange output; the sensitive code; the written rules.
  Leave out your own reasoning about the design: the sub-agents should see the code, not
  its justification.

The depth of the analysis follows the reach, not the size of the diff. A three-line
change gets the full method; only the report gets shorter.

### 2. Scenarios

Spawn one fresh sub-agent, not a fork of your context. Give it the brief, the Terms, and
the absolute path of `references/lenses.md` in this skill's base directory, with the
task to follow its Scenarios section. It returns 3 scenarios per area. It never sees an
alternative design: scenarios chosen after the designs flatter a favorite.

Show the scenarios to the human, one line each with where its likelihood comes from
(git history, the ticket, a requirement), and ask them to confirm, edit or replace them.
Wait for the answer: the human knows the domain, and the scenarios decide what the
counts mean. If the human said not to wait, or no human is in the loop, go on and mark
the scenarios as unconfirmed in the report.

### 3. Versions and counts

Spawn two fresh sub-agents in parallel, per area. Give both the brief, the confirmed
scenarios, this skill's intro, Terms, The three lenses, the rules below, and the absolute
paths of `references/lenses.md` and `references/moves.md` in this skill's base directory.

- **The layer pass** looks for versions that move knowledge to the layer or object that
  owns it: a rule next to the data it reads, a side effect out of a callback, fetching
  out of display code, a framework's own home for that kind of code.
- **The seam pass** looks for versions that split or merge units and change their
  interfaces: a split along groups of methods that share no state, a merged pass-through,
  one state value instead of several flags, a value object, one map or polymorphism
  instead of the same branch in several places.

Rules for both passes:

- You report; you don't edit any file.
- Propose at most 2 versions that lower the counts. A version is a concrete design that
  names each unit it adds, moves, merges or deletes, with file paths. A principle is not
  a version.
- Where this repo has a way of doing this kind of thing (at least 3 existing siblings, or
  a written rule), follow it. A version that introduces a new way says so, and counts the
  siblings that would then do it differently.
- Count V0 yourself, independently of the other pass.
- Count every version as `references/lenses.md` describes: the edit list per scenario,
  the behavior cases and their test levels, the read question and its files.
- Then state, per version, the principles or patterns it relies on as predictions:
  "<principle> predicts <which count> improves for <scenario>".
- Mark what touches sensitive code, what changes intended behavior (what changes, and
  who would notice), and the existing churn.
- Note bugs you notice in one line each, with the input that triggers them. Note local
  waste (dead checks, wrappers that only forward) in one line in total; trim-code covers
  it.
- Return the format below, and stay under 800 words.

```
Area: <name>
Behavior cases: C1 <case>, C2 <case>, …
Read question: "<question>"

V0 as written
  S1 4u 35l: orders_controller.rb#create 12l, order_mailer.rb#confirm 8l (lockstep), …
  S2 …   S3 …
  Test: C1 request 25l, C2 request 22l, … = 120l; unit 0, integration 5, end-to-end 0
  Read: 4 files: orders_controller.rb, order_mailer.rb, …
V1 <short name>: <what changes: units added, moved, merged, deleted, with paths>
  S1 … S2 … S3 …   Test …   Read …
  Concepts: +Order::Checkout −DiscountService
  Predictions: <principle> predicts <count> for <scenario>
  Touches: existing churn <files, ~lines>; sensitive <none or what>; behavior <kept, or what changes>
Bugs: …
Local waste: …
```

### 4. Verify and sort

- **Noise check.** Compare the two passes' V0 counts. If they differ beyond the win
  threshold, recount V0 yourself and use your count.
- **Merge** versions the two passes both found. Number the rest V1, V2, … across all
  areas.
- **Verify** every version that could be applied or recommended. The units it names
  exist. Moved code can reach what it needs from its new home, without a circular
  dependency, and is not a callback the framework calls by name. Recount the scenario
  where it claims its biggest win. A claim that doesn't hold kills the version: "the
  evidence didn't hold". Agent suggestions about where code belongs are often invalid
  until checked like this.
- **Predictions:** mark each one ✔ held, ✘ failed, or ~ partly held.
- **Sort** with the rules in Three lists. When two winning versions conflict, the larger
  win without sensitive code goes on Apply. The other goes to Your call if it goes
  further, otherwise to Not pursued.
- **Cap:** at most 3 Your call versions per report. The others go to Not pursued as
  "smaller win than V<n>".
- A certain bug with a local fix in the diff goes on Apply, with a test that would have
  caught it. Any other bug goes to Your call.

### 5. Apply and clean up

For each Apply version, largest win first:

1. **Measure.** In a throwaway git worktree with the diff applied, implement the version,
   then the scenario with its biggest claimed win, and take the real line and unit
   counts from `git diff --stat` and the edit itself. Do the same for that scenario on
   V0. If the measured win falls under the threshold, move the version to Not pursued as
   "measured: a tie". Remove the worktree afterwards.
2. **Pin down.** Code that the version reshapes and no test covers gets tests capturing
   its current behavior first.
3. **Apply** it to the working tree. Tests move with the code, to the level the Test
   lens promised: check that they really did.
4. **Clean up, always:**
   - The old path is gone: no forwarding methods, shims, aliases or re-exports left for
     callers the diff already updated. Old and new side by side is more concepts than
     before: finish the move or revert it.
   - Nothing is orphaned: imports, helpers, fixtures, factories, translations, routes,
     styles the move left behind.
   - Tests of deleted code are deleted with it.
   - Comments and docs that name the old location are updated.
5. **Run** the tests for the touched files, the tests of their callers and the feature's
   end-to-end tests, plus the linters for the touched files, using the project's fastest
   runner. If they fail, find the version that broke them, revert only that one, and move
   it to Your call with the failure. A test of intended behavior is never changed to
   make it pass.

Never discard the diff's own work. Don't commit unless the human asks.

### 6. Report

Rules:

- One block per area, at most about 12 lines each, under one heading for the whole diff.
- In the matrix, V0 shows absolute counts, like `4u 35l`. Other versions show the
  difference from V0, like `−3u −25l`, and `–` for a tie. `u` is units and `l` is lines
  of logic. The Test column shows lines, then the cases per level as
  unit/integration/end-to-end.
- One line per decision: its emoji, its code, its name, the numbers that decided it,
  then cost and risk where there are any. A line wraps at most once.
- Predictions go on one line, and the takeaway on one line: the principle that held in
  this diff, phrased as the question the human can ask next time.
- No prose paragraphs, no restating the method, no list of files read. Code names and
  numbers carry the report.

```
## Shape: loyalty discount (14 files, 2 areas)
Scenarios: S1 seasonal discount · S2 discount via API · S3 cap per customer

Discount rule      S1         S2         S3         Tests (6 cases)   Read
V0 as written      4u 35l     3u 40l     4u 30l     120l 0/5/0        4
V1 rule on Order   −3u −25l   −2u −32l   −2u −15l   −75l 6/0/0        −2
V2 + policy obj    −3u −23l   −2u −32l   −3u −20l   −70l 6/0/0        −1

✅ V1 rule on Order: wins all three, tests leave the request level. Measured S2 −30l (est. −32l).
🛠️ V2 policy object: −1u more on S3 only, +1 file on Read, +1 concept → worth it if per-customer caps are planned.
🚫 Service object: +1 Read, no scenario gain · Concern: moves lines, changes no count
Predictions: SRP → fewer units for S3 ✔ only S3 · Strategy pattern ✘ one kind, +2 concepts
Takeaway: does the rule read only Order's data? Then it lives on Order (−3u for S1).
Tests: order_spec, orders_request_spec, checkout e2e ✔
```

Below the areas, one line for areas not shaped, and one for bugs (🐞) and local waste
if any: suggest `/trim-code` there, and run it after this skill, not before: trimming
first can delete the duplication that is evidence for a move. If there are Your call
versions, end with one line: `apply V2` to apply one.

If another skill called this one, hand it the report.

### 7. Your call

The human approves versions by code, like `apply V2`. Carry each one out as in step 5,
measurement included. For a behavior change, the plan also names what exactly changes
and which tests assert the old behavior: update those, and delete the ones that only
covered it. If a version turns out weaker than reported, say so in one line and don't
apply it.

## Checking this skill

Backtest before trusting it on a codebase. Take 3–5 older commits whose code later
features changed, and run the skill as of each commit. Then compare with the real
history: did the scenarios predict the kinds of change that came, and would the winning
version have made the real later commits smaller? Scenarios that miss the real changes,
or wins that don't show up in history, mean the scenario step or the counting needs
work, not the report.
