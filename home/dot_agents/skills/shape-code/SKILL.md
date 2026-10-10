---
name: shape-code
description: >-
  Measures how robust a working change is for whatever comes next, with counts instead of
  opinions. Lists every decision the code makes (rules, data fields, formats,
  permissions, interfaces, outside libraries, the feature itself) and counts, for the
  change as written and for alternative designs, how many places would change if each
  decision changed, how much each test has to set up, and how many files a reader opens
  to understand the behavior. Recommends the shape that puts decisions in one place
  without making testing or reading harder, states design principles only as predictions
  the counts confirm or refute, and changes code only when asked. Use after implementing
  a change that works, when asking whether code is in the right place (MVC layer, model
  vs controller vs service, how to split a component), whether a pattern like a service
  object, form object or store pays off, how maintainable or testable a change is, or to
  train one's own design judgement on real diffs.
argument-hint: "[base ref or commit range]"
---

# Shape code

Agents write code that works, and a reader checks it for correctness. Whether everything
is in the right place rarely gets asked, and asked as "is X better than Z?" it has no
answer anyone can check. This skill asks a question that does: **if something this code
decides changes, how many places change with it?** A shape is robust for whatever comes
next when each decision lives in one place, its rules can be tested with little setup,
and a reader finds them without a tour. That needs no guess about the future: every
future change touches some decision the code already makes.

The skill counts, and the counts decide. Principles and patterns come last, as
predictions the counts confirm or refute for this code; a principle is never a reason on
its own. A pattern is neither good nor bad in itself: the same service object, form
object or store wins in one diff and only adds files in another.

The report is the product: a matrix and one line per verdict, scannable in a few
seconds. A long or overwhelming report is a failed run, however good the analysis behind
it. The skill analyzes; it changes code only when the human asks.

## Terms

- **The diff** is the change being shaped: a commit range or uncommitted work.
- **Existing code** is every line the diff neither adds nor modifies.
- **Existing churn** is the lines of existing code a version modifies, moves or deletes,
  renames and updated call sites included.
- **Intended behavior** is what the requirements, specifications or docs ask for, what
  tests pin down, and what code in this codebase relies on. A detail nobody could sensibly
  rely on (key order, whitespace, a typo in a message) doesn't count.
- **A unit** is anything with a name a reader navigates to: a method, function, class,
  module, component, template or config entry.
- **A decision** is something the code commits to that could change on its own: a
  business rule, a data field and where it flows, a display format, a permission, an
  interface the diff creates or widens, an outside library the code calls directly, and
  the existence of the feature itself.
- **Places** of a decision are the units that would have to change if that decision
  changed, anywhere in the codebase, not only in the diff's files. **Lockstep** places
  must change together, or behavior breaks.
- **The history** of a decision is how often git shows its places changing together in
  past commits. It sets how urgent a spread decision is, not whether it matters: a
  decision spread over several places is worth fixing either way, sooner when its places
  keep changing together.
- **A version** is a design of the diff. **V0** is the diff as written. V1, V2, … are
  alternatives.
- **The reach** of the diff is the diff plus what it plugs into: its callers, the rules
  and structures it extends, and the files git history shows changing with it. Counts
  cover the reach: a small change often costs through where it lands.
- **An area** is a part of the diff that can be judged on its own, like a rule and its
  consumers, or a screen. Most diffs are one area.
- **Sensitive code** is code where a small mistake is expensive: money, access
  (authentication, sessions, permissions), writes to persistent data and migrations,
  public contracts (APIs, events, URLs, file formats), checks on outside input,
  concurrency and caching, and untested hot spots. Judge it from the code and its
  history.

## The three lenses

Each lens is a count. The sub-agents count by [references/lenses.md](references/lenses.md).

1. **Decisions** (the main lens). Every decision in the reach, with its places in each
   version, which of them are lockstep, and its history: 🔥n when its places changed
   together in n past commits.
2. **Test.** The behavior cases, listed once. For each version: what a test of each case
   has to set up (records, factories, logins, providers, mocks, spies, HTTP fakes,
   fixtures) and its lines. Setup per case makes framework weight visible: a rule in a
   plain function needs almost none, the same rule in a component under a test bed needs
   a lot.
3. **Read.** For one concrete question about the behavior ("what discount does order 42
   get?"): the files a reader opens to answer it.

A supporting number, shown only when it applies: **invalid states**, when the diff adds
flags or optional fields that together describe one state ("3 flags: 4 of 8 combinations
valid").

**Decisions lead; Test and Read are guardrails.** A version beats V0 when:

- it brings at least one decision from several places to one, or removes lockstep places,
  or removes at least 2 places in total; or, on Test alone, it moves at least 5 cases to
  a setup of about 1 or less;
- it adds at most one file to Read for each decision it brings to one place;
- and it is no worse on Test beyond noise.

Smaller differences are ties. Counts are estimates; a tie is reported as one.

**Urgency.** Among winning versions, the ones that bring a decision with history (🔥) to
one place rank first: that cost has been coming due. A version that only fixes spread
decisions without history still wins and is still recommended, marked as less urgent.

**Counts can be gamed.** Shorter but denser doesn't count: packed lines, long call chains,
clever tricks, metaprogramming where two plain cases would do. Every concept a version
adds (a class, an object, a flag or mode an abstraction branches on, a pattern) is listed
next to its counts.

**No speculation.** A version must lower counts for decisions the code makes today. A
seam, registry or strategy built for a variant that doesn't exist yet wins nothing here.
Future work enters only when the human names it (step 1); it is then counted as an extra
row and marked as such.

## Three lists

Every version ends on one list.

- ✅ **Recommended.** It wins on the rules above and keeps the intended behavior. Its
  existing churn stays at most about twice the lines it saves; for a version that brings
  a decision with history (🔥) to one place, up to about five times, because history
  shows that cost comes due anyway.
- 🛠️ **Trade-off.** Worth considering, but the human has to weigh it: the lenses disagree,
  it changes intended behavior, reaches far into existing code, touches sensitive code,
  adds a dependency or a schema change, or introduces a way of doing things this repo
  doesn't use yet. A new way is not a reason to drop a version: count the siblings that
  would then do it differently, and let the human decide.
- 🚫 **Not pursued.** No win beyond noise, worse on a lens, a prediction that failed,
  evidence that didn't hold, or it contradicts a choice the human already made. One line
  each.

## Steps

Track these steps in your todo list:

```
- [ ] 1. Scope: the diff, the reach, the decisions, sensitive code, cochange output
- [ ] 2. Versions counted by both passes
- [ ] 3. Counts verified, predictions checked, versions sorted
- [ ] 4. Report
- [ ] 5. Apply only what the human picks
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
  prints hot spots and the files that change together with the diff's files.
- Read the project's written rules: `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`,
  `REVIEW.md`, `docs/adr/`, architecture docs. Choices recorded there are settled unless
  a count shows a real cost; then the version is a Trade-off naming the choice.
- Map the reach, and mark the sensitive code in it.
- **List the decisions** in the reach, by the kinds in Terms, with their places in V0.
  Search the whole codebase for each decision's places: a rule the diff touches often
  lives on in older files too. Then look up each spread decision's history as
  `references/lenses.md` describes. This list is shared by everyone, so every version is
  counted against the same rows.
- **Future work** counts only if the human named it ("we'll add multi-currency next").
  Add it as a row marked `planned`. Don't invent future work.
- **Areas:** most diffs are one area. Split a large diff into at most 3 areas, the ones
  with the most decisions in several places. Name the rest in the report as not shaped.
- **The brief** for every sub-agent: the requirements in the human's or the ticket's own
  words; choices the human already made (what, not why); questions the human asked,
  quoted; the diff command; the reach; the decision list; the cochange output; the
  sensitive code; the written rules. Leave out your own reasoning about the design: the
  sub-agents should see the code, not its justification.

The depth of the analysis follows the reach, not the size of the diff. A three-line
change gets the full method; only the report gets shorter.

### 2. Versions and counts

Spawn two fresh sub-agents in parallel, per area, not forks of your context. Give both
the brief, this skill's intro, Terms, The three lenses, the rules below, and the absolute
paths of `references/lenses.md` and `references/moves.md` in this skill's base directory.

- **The layer pass** looks for versions that move knowledge to the layer or object that
  owns it: a rule next to the data it reads, a side effect out of a callback, fetching
  out of display code, a framework's own home for that kind of code.
- **The seam pass** looks for versions that split or merge units and change their
  interfaces: a split along groups of methods that share no state, a merged pass-through,
  one state value instead of several flags, a value object, one map instead of the same
  branch in several places.

Rules for both passes:

- You report; you don't edit any file.
- Propose at most 2 versions. A version is a concrete design that names each unit it
  adds, moves, merges or deletes, with file paths. A principle is not a version.
- Count V0 yourself, independently of the other pass. Add decisions the list missed, and
  say so.
- Count every version as `references/lenses.md` describes: places per decision, setup and
  lines per test case, files to read.
- Where this repo has a way of doing this kind of thing (at least 3 siblings, or a
  written rule), say whether the version follows it. A version that introduces a new way
  counts the siblings that would then differ.
- State, per version, the principles or patterns it relies on as predictions:
  "<principle> predicts <which count> improves".
- Mark what touches sensitive code, what changes intended behavior (what changes, and
  who would notice), and the existing churn.
- Return the format below, and stay under 800 words.

```
Area: <name>
Decisions (V0 places; ⛓ = lockstep; 🔥n = places changed together in n past commits):
  D1 what "active account" means: 4 places ⛓ 🔥4 (accounts_controller.rb#index, family.rb#series, …)
  D2 …
Behavior cases: C1 <case>, C2 <case>, …
Read question: "<question>"

V0 as written
  Test: C1 request, setup 3 (family, user, login), 22l; … = 120l, setup 3.0/case
  Read: 4 files: …
V1 <short name>: <what changes: units added, moved, merged, deleted, with paths>
  Decisions: D1 1 (account.rb scope :active), D2 …
  Test …   Read …   Invalid states …
  Concepts: +Account.active −Family#active_accounts
  Predictions: <principle> predicts <count> improves
  Touches: existing churn <files, ~lines>; sensitive <none or what>; behavior <kept, or what changes>; repo way <follows, or new: N siblings differ>
Local waste: … (one line; trim-code covers it)
```

### 3. Verify and sort

- **Noise check.** Compare the two passes' V0 counts. Where they differ by more than one
  place on a decision, or more than about 30% on Test, recount it yourself.
- **Merge** versions the two passes both found. Number the rest V1, V2, … across areas.
- **Verify** every version you would recommend or offer. The units it names exist. Moved
  code can reach what it needs from its new home, without a circular dependency, and is
  not a callback the framework calls by name. Recount the decision where it claims its
  biggest win. A claim that doesn't hold kills the version: "the evidence didn't hold".
  Agent suggestions about where code belongs are often invalid until checked like this.
- **Predictions:** mark each one ✔ held, ✘ failed, or ~ partly held.
- **Sort** with the rules in Three lists. When two recommended versions conflict, keep
  the one with the larger win as Recommended and the other as Trade-off.
- **Cap:** at most 3 versions in the matrix per area, Recommended and Trade-offs
  together. Merge versions that build on each other into one; the others go to Not
  pursued as "smaller win than V<n>".

### 4. Report

Rules:

- One block per area, at most about 15 lines each, under one heading for the whole diff.
- The matrix has a row per decision and a column per version, V0 and at most 3 more.
  Show the decisions that differ between versions or sit in more than one place;
  summarize the rest in one row, like `+5 decisions at 1 place in every version`. ⛓
  marks lockstep places, 🔥n the history. The last two rows are Tests and Read.
- Every number carries its unit, so the matrix reads without a legend: `4 places`,
  `120 lines · 3.4 setup items/case`, `5 files`. Below the matrix, one line names what
  the setup items are, like `setup items: records, login, mocks, TestBed providers`. Show
  each version's own counts from the passes; never one blended figure for all columns.
- One line per verdict: its emoji, its code, its name, the numbers that decided it, then
  cost and risk where there are any. A line wraps at most once.
- Predictions go on one line, and the takeaway on one line: the question the human can
  ask themselves next time, with this diff's answer.
- No prose paragraphs, no restating the method, no list of files read.

```
## Shape: accounts list (12 files, 1 area)

Decision (places)                 V0                    V1 scope on Account   V2 + series in one method
what "active account" means 🔥4   4 ⛓                   1                     1
how balances become series 🔥3    3                     3                     1
which accounts are listed         2                     1                     1
+4 decisions at 1 place in every version
Tests (7 cases)                   140 lines · 3.4/case  90 lines · 1.6/case  85 lines · 1.6/case
Read                              5 files               4 files               4 files
setup items per case: records, login, request

✅ V2 series in one method: "active" 4→1 places 🔥, series 3→1 🔥, setup 3.4→1.6/case, −1 file.
🛠️ V1 scope only: smaller step ("active" 4→1, listing 2→1), leaves the series in 3 places 🔥.
🚫 Service object for the list: +1 Read file, no decision moves · Store/presenter: same
Predictions: rule with its data → D1 one place ✔ · service object → fewer places ✘ none moved
Takeaway: if "active" changed, how many files would you edit? 4 here; a scope on Account makes it 1.
```

Below the areas: one line for areas not shaped, one for bugs noticed (🐞) if any, one
for local waste with a pointer to `/trim-code` if any. End with one line:
`apply V2` to have one applied.

If another skill called this one, hand it the report.

### 5. Apply only what the human picks

The human picks versions by code, like `apply V2`. For each:

1. **Pin down.** Code that the version reshapes and no test covers gets tests capturing
   its current behavior first: written against the code as it is, using only what
   exists before the change, and run green on it before anything moves. A pin-down
   test that calls the new code pins nothing. If tests can't run here, say so, and still
   write them against the old code.
2. **Apply** it. Tests move with the code, to the setup the Test lens promised: check
   that they really did. For a behavior change, update the tests that assert the old
   behavior and delete the ones that only covered it.
3. **Clean up, always:**
   - The old path is gone: no forwarding methods, shims, aliases or re-exports left.
     Old and new side by side is more concepts than before: finish the move or revert it.
   - Nothing is orphaned: imports, helpers, fixtures, factories, translations, routes,
     styles the move left behind. Tests of deleted code go with it.
   - Comments and docs that name the old location are updated.
4. **Run** the tests for the touched files, the tests of their callers and the feature's
   end-to-end tests, plus the linters for the touched files. If they fail, revert only
   that version and say why. A test of intended behavior is never changed to make it
   pass.

If a version turns out weaker than reported while planning it, say so in one line and
don't apply it. Never discard the diff's own work. Don't commit unless the human asks.

## Checking this skill

Backtest before trusting it on a codebase. Take 3–5 older commits whose code later
changed, and run the skill as of each commit. Then compare with the real history: did
the real later commits have to edit the decisions the report showed as spread over
several places, and would the recommended version have made those commits smaller?
