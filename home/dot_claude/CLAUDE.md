# Global Instructions

## Verification before claiming

Never state that behavior is covered, fixed, or that an API raises/returns X without empirical proof in this session. Run the test, the console probe, or the debugger and paste the output. If you cannot verify, say "unverified" explicitly and state what probe would confirm it.

## Test-First Workflow

For any non-trivial change, and especially for bug fixes, write tests first and confirm the tests are failing before implementing the required change or fix.

Once the fix is green, mutation-verify it: revert the production change, confirm the test goes red again, then restore it. Paste both outputs. A test that cannot be made to fail proves nothing — if you cannot produce a red state, say so explicitly instead of reporting the behavior as covered.

## Manual QA / walkthroughs

When the user asks to "walk through", "step through", or "manually QA" something: write each step as a small numbered task script, run it, and report the observed output together with the one-line command to re-run it. Never seed data silently — the script is the record and must be readable before it runs. Checks only a human can judge (rendering, interaction, timing) are handed over one at a time.

## Scope Discipline

- Make the minimum change requested. Do not add defensive nil guards, remove unrelated code, or refactor adjacent tests unless explicitly asked.
- When refactoring, preserve existing API and behavior surface unless the user asks to change it.
- If an adjacent change seems warranted, propose it first — do not bundle it in.
- Do not modify shared helpers without explicit justification tied to a failing test or stated requirement.

## Investigation Before Action

- Do not guess at config option names, defaults, or API semantics. Verify via official docs, source, or a command first.
- For any config change, cite the exact doc section or source line that documents the option before proposing it. If you can't find documentation, say so explicitly rather than guessing.
- For CI vs local discrepancies, verify tool versions and config on both sides before concluding.
- If the user says "find it out" or similar, that's a signal you jumped to a guess — back up and investigate.
- Before implementing, present the design decisions a reviewer will have opinions on as a short approach note and wait for direction: new data formats, where files live, new routes or top-level classes, and hand-rolling something an installed library or framework helper already does. A rejected design after review costs a full rewrite, and the rewrite restarts the review.

## Code Style / Simplicity

- Favor the simplest approach: avoid alias methods, separate migrations with dedup SQL, or over-engineered abstractions unless explicitly requested. Inline and simplify by default; ask before adding complexity.
- When introducing a new API or method, keep it as minimal as possible and never abstract prematurely. The final shape depends on the developer's taste — I will give the direction on how to structure it. Minimal, literal code helps me and reviewers understand and verify how it works.
- Don't invent abstractions (new classes, modules, options, generic helpers) for reuse that hasn't happened yet; wait until the third repetition. Placing code where the framework's conventions put it is not abstraction; always do that: data lookups and sorting on the model/domain class, not in a controller; HTML in views, partials or helpers, not in a model. Project rules and the maintainer's conventions override these defaults.
- Prefer an installed library or framework helper over a hand-rolled parser, regex or literal path (e.g. Rails asset helpers instead of `/favicon.png`). Prefer the conventional pattern over a clever one (e.g. BEM modifier classes over `:has()` selectors).
- Simplicity is also *removing* code, not only avoiding abstraction. Don't add `if` guards, defensive re-checks, or parsing for cases the underlying call or surrounding code already handles correctly (e.g. checking `HEAD` exists before `git diff`, which already handles an empty repo). When a branch can't be reached or a check the callee already makes, delete it.
- Default to no comments on new code; make it self-explanatory through naming and structure. Where a project rule allows a narrow exception (e.g. a 1–2 line note on a non-obvious workaround), follow that rule.

## Rails / Database Conventions

- Prefer DB-level operations over in-memory Ruby: use `order` for sorting and avoid `sort_by`, scope transactions tightly, and watch for N+1 queries by preloading associations.

## Testing & Fixtures

- When a fixture breaks on a schema change, treat it as a fixture-only problem where possible; use the `_fixture model_class` approach for non-conventional table names. How migrations are split is the project's migration rule's call.
- Every bug fix needs its own explicit regression test. Incidental fixture coverage does not count as coverage.
- Prefer dedicated focused unit tests over extending large cascade tests.
- Run RuboCop only against Ruby files; never against `.yml` fixtures.

## Editing & File State

- Do not verify or claim files are unchanged until the user confirms they have saved; never rely on stale file state before reporting status.

## Communication Style

- Explain technical concepts in plain language first; avoid jargon-heavy compressed answers and unpack reasoning step by step.
