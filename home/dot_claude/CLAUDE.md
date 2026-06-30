# Global Instructions

## Test-First Workflow

For any non-trivial change, and especially for bug fixes, write tests first and confirm the tests are failing before implementing the required change or fix.

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

## Code Style / Simplicity

- Favor the simplest approach: avoid alias methods, separate migrations with dedup SQL, or over-engineered abstractions unless explicitly requested. Inline and simplify by default; ask before adding complexity.
- When introducing a new API or method, keep it as minimal as possible and never abstract prematurely. The final shape depends on the developer's taste — I will give the direction on how to structure it. Minimal, literal code helps me and reviewers understand and verify how it works. Favor JRY (Just Repeat Yourself) over DRY here: prefer repetition over speculative abstraction.

## Rails / Database Conventions

- Prefer DB-level operations over in-memory Ruby: use `order` for sorting and avoid `sort_by`, scope transactions tightly, and watch for N+1 queries by preloading associations.

## Testing & Fixtures

- When testing migrations/fixtures, fold index/constraint changes into the existing migration and treat schema issues as fixture-only problems where possible; use the `_fixture model_class` approach for non-conventional table names.

## Editing & File State

- Do not verify or claim files are unchanged until the user confirms they have saved; never rely on stale file state before reporting status.

## Communication Style

- Explain technical concepts in plain language first; avoid jargon-heavy compressed answers and unpack reasoning step by step.
