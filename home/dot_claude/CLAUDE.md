# Global Instructions

## Verification before claiming

Never state that behavior is covered, fixed, or that an API raises/returns X without empirical proof in this session. Run the test, the console probe, or the debugger and paste the output. Check that the output shows the intended effect for the intended reason, not just that the command ran: look at the diff after a scripted edit, and read why a test failed before counting it as red. If you cannot verify, say "unverified" explicitly and state what probe would confirm it.

## Test-First Workflow

For any non-trivial change, and especially for bug fixes, write tests first and confirm the tests are failing before implementing the required change or fix.

Once the fix is green, mutation-verify it: revert the production change, confirm the test goes red again, then restore it. Paste both outputs. A test that cannot be made to fail proves nothing — if you cannot produce a red state, say so explicitly instead of reporting the behavior as covered.

## Manual QA / walkthroughs

When the user asks to "walk through" or "step through" something, go turn by turn: each turn covers one small piece of information, then stop and wait for the user before the next. Never deliver the whole walkthrough as one wall of text.

When the user asks to "manually QA" something, or a walkthrough step needs to run something: write each step as a small numbered task script, run it, and report the observed output together with the one-line command to re-run it. Never seed data silently — the script is the record and must be readable before it runs. Checks only a human can judge (rendering, interaction, timing) are handed over one at a time.

Every task script, in any mode or skill, ends its header comments with a debug hint, so I can stop on any line and know where to read more. Never run a script that has a live breakpoint: without a terminal the debugger either quits at it with exit 0 or hangs waiting for input, and the rest of the script never runs.

Ruby: `bin/rails runner` and `bin/rails test` get `debugger` from the Gemfile's `debug/prelude`; a plain `ruby` script gets `require('debug')` as its first code line.

```ruby
# Debug: add `debugger` on any line, then run line 1 in a terminal pane (tests: prefix PARALLEL_WORKERS=1).
#   At (rdbg): p x, info, n next, s step, c continue, help. More: https://github.com/ruby/debug#debug-command-on-the-debug-console
```

Node:

```js
// Debug: add `debugger;` on any line, run `node inspect <script>` in a terminal pane and c to reach it.
//   At debug>: exec x, n next, s step, c continue, .exit. More: https://nodejs.org/api/debugger.html
```

Shell:

```bash
# Debug: `set -x` on any line traces every command from there, `set +x` stops; Ruby it runs takes `debugger`.
```

## Scope Discipline

- Make the minimum change requested. Do not add defensive nil guards, remove unrelated code, or refactor adjacent tests unless explicitly asked.
- When refactoring, preserve existing API and behavior surface unless the user asks to change it.
- If an adjacent change seems warranted, propose it first — do not bundle it in.
- Do not modify shared helpers without explicit justification tied to a failing test or stated requirement.

## Investigation Before Action

- Don't fill a gap with a plausible guess. When a fact can be looked up (code, data, branch, installed libraries, tool behavior, docs), look it up first; when only I know it (which environment, what I meant), ask.
- Before solving something, look at how this project already does it (tooling, skills, config files, test style) and do it that way. A choice I made or reverted stays decided.
- For any config change, cite the exact doc section or source line that documents the option before proposing it. If you can't find documentation, say so explicitly rather than guessing.
- For CI vs local discrepancies, verify tool versions and config on both sides before concluding.
- If the user says "find it out" or similar, that's a signal you jumped to a guess — back up and investigate.
- Before implementing, present the design decisions a reviewer will have opinions on as a short approach note and wait for direction: new data formats, where files live, which class owns new logic, new routes or top-level classes, and hand-rolling something an installed library or framework helper already does. A rejected design after review costs a full rewrite, and the rewrite restarts the review.

## Code Style / Simplicity

- Choose the simplest approach that works. Inline by default and ask before adding complexity.
- Keep new APIs minimal and literal, so I and reviewers can verify them. Their final shape is my call; wait for my direction.
- Don't abstract for reuse that hasn't happened yet; wait until the third repetition. Putting code where the framework's conventions put it is not abstraction; always do that. Project rules and the maintainer's conventions override these defaults.
- Use what installed libraries and the framework already provide instead of hand-rolling it, and prefer the conventional pattern over a clever one.
- Simplicity also means removing code: don't guard against cases the callee or surrounding code already handles, and delete branches that can't be reached.
- No comments on new code by default; let naming and structure explain it. Follow a project rule that allows a narrow exception.

## Rails / Database Conventions

- Prefer DB-level operations over in-memory Ruby: use `order` for sorting and avoid `sort_by`, scope transactions tightly, and watch for N+1 queries by preloading associations.
- Reek exemptions go in `.reek.yml` with a comment in that file saying why, never inline in the source.

## Testing & Fixtures

- When a fixture breaks on a schema change, treat it as a fixture-only problem where possible; use the `_fixture model_class` approach for non-conventional table names. How migrations are split is the project's migration rule's call.
- Every bug fix needs its own explicit regression test. Incidental fixture coverage does not count as coverage.
- Prefer dedicated focused unit tests over extending large cascade tests.
- Run RuboCop only against Ruby files; never against `.yml` fixtures.

## Editing & File State

- Do not verify or claim files are unchanged until the user confirms they have saved; never rely on stale file state before reporting status.

## Communication Style

- Explain technical concepts in plain language first; avoid jargon-heavy compressed answers and unpack reasoning step by step.
