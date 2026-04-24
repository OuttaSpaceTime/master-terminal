# Intent Buckets

Used by `/diff-review` Checkpoint 1 when labeling file leaves and rolled-up tree groups in
the HTML overview. Pick exactly one bucket per file. Group badges should follow the
dominant bucket in that subtree; if the subtree is genuinely mixed, use `Mixed`. When
unsure on a file, use `Other` rather than forcing a fit — a wrong bucket is worse than a
vague one because it misleads orientation.

## The eight buckets

| Bucket | When to use | Color dot |
|---|---|---|
| `Feature` | Adds new user-visible behavior or a new code path that didn't exist before. | 🟢 |
| `Fix` | Corrects broken behavior. Includes regressions, off-by-one, wrong defaults, missing null checks where the absence caused observable failure. | 🔴 |
| `Refactor` | Restructures existing code without changing observable behavior — extractions, renames, inlining, splitting modules. | 🟣 |
| `Test` | Adds, modifies, or deletes test files. Test fixture changes count as `Test`, not `Config`. | 🧪 |
| `Docs` | README, comments-only changes, ADRs, in-repo docs sites. JSDoc/RST/godoc on otherwise-changed code does NOT make the file `Docs` — bucket by the dominant change. | 🔵 |
| `Config` | Build files, dependency manifests, lint/format configs, CI YAML, env templates, deployment manifests. | 🟡 |
| `Types` | Type-only files (`.d.ts`, type-alias modules, schema declarations). If a type change rides alongside a behavior change in one file, pick the behavior bucket. | ⚪ |
| `Other` | Anything that doesn't cleanly fit. Use freely — a `Other` row is honest; a wrong bucket is misleading. | ⚫ |

## Rules of thumb

1. **One bucket per file.** Don't compound — pick the dominant change.
2. **Behavior beats shape.** A file that gains both a new function and a new type is `Feature`, not `Types`.
3. **Test fixtures travel with tests.** A new JSON fixture under `__fixtures__/` is `Test`, not `Config` or `Other`.
4. **Generated/auto-formatted files** — bucket by their original purpose if known, otherwise `Other`.
5. **Renames and pure deletions** — use the bucket of the change's intent (e.g., a rename done for clarity is `Refactor`; a deletion as part of removing dead code is `Refactor` or `Other`).
6. **When you're about to write `Refactor` for a file you also clearly added behavior to** — it's `Feature`. Prefer the more visible bucket.

## CSS class mapping (used by the HTML template)

`Feature` → `b-feature` · `Fix` → `b-fix` · `Refactor` → `b-refactor` · `Test` → `b-test` ·
`Docs` → `b-docs` · `Config` → `b-config` · `Types` → `b-types` · `Other` → `b-other`
