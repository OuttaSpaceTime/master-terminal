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
