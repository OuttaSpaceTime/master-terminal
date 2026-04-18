---
name: sketch
description: "Quick draft diffs for a small, well-understood change (1-5 files) — no interaction or iterations. Produces a file-impact table, affected tests, and diff blocks as a saved planning document. Planning only — never applies code. Distinct from /plan (sequenced strategy for larger or uncertain changes) and /scout (exploratory scoping before you understand the code)."
---

# Sketch

Draft diffs with context, a file-impact table, and affected tests for a small-scope change. **No code is applied — output is a saved planning document only.**

## When to Use Sketch (and When Not To)

**Use `/sketch` when:**
- You have already read the affected files (or will read them as step 1)
- The change affects **fewer than 5 files**
- No architectural unknowns remain — you know exactly what to change

**Use `/plan` instead when:**
- Scope is uncertain or still being defined
- The change touches **5+ files**
- Architectural unknowns exist (e.g., unclear how subsystems interact)

**Use `/scout` instead when:**
- You have not yet explored the affected code
- You need to understand the problem before proposing a solution

**Do NOT sketch if:**
- You have not read the files yet — read first, sketch second
- Scope is uncertain — clarify scope first (via `/scout` or discussion)
- The change touches 5+ files in unfamiliar code — use `/plan` to sequence the work

## Workflow

> **Chaining:** If a `/scout` or `/plan` report exists for this change, read it first. Extract the file list and high-confidence facts. Use those to guide file-reading order. Do not re-explore what those reports already established.

### 1. Read Every File You Will Diff

- Use Grep/Glob to locate files if needed, then Read each file before drafting its diff. No exceptions — diffs based on assumptions produce incorrect sketches.
- Match the existing code exactly: variable names, import paths, indentation, conventions.

### 2. Produce Diff-First Sketch

- Start with a TL;DR (2-3 bullets: what changes, why, and what is explicitly out of scope).
- One `### path/to/file` section per file, each containing one or more `diff` blocks.
- Include 2-3 lines of unchanged context around each hunk.
- Separate unrelated changes within a file into distinct hunks.
- For new files: show the full proposed content in a plain code block (not diff format).

### 3. Fill Impact Tables

- **File Impact table:** every touched file with impact type (create / modify / delete) and one-line reason. Include files that are only read as consumers if their behavior depends on the change.
- **Affected Tests table:** spec files and checks that need updating, with expected changes.
- Add a "Compatibility Notes" section only if the change affects APIs, migrations, or integrations.

### 4. Save and Present

- `mkdir -p .claude/docs/sketches` then write to `.claude/docs/sketches/YYYYMMDD-<topic>.md`.
- Present the full sketch in chat. End with the saved file path so the user can reference it later.

## Output Template

~~~markdown
# <Topic> - Sketch

## TL;DR
- <what changes>
- <why>
- Scope: <explicit boundary — what is NOT included>

## File Impact
| File or Area | Impact | Reason |
| --- | --- | --- |
| <path> | create / modify / delete | <short reason> |

## Affected Tests / Checks
| Test or Check | Why Impacted | Expected Update |
| --- | --- | --- |
| <path or name> | <short reason> | <short update> |

## Draft Diffs (Not Applied)
### `<path/to/file.ext>`
<one-line intent>

```diff
  context
- old line
+ new line
  context
```

(Repeat for each file.)

## Compatibility Notes (Only If Relevant)
- <migration/api/job/email/integration impact>

## Open Questions
- <only blocking unknowns>
~~~

## Rules

<critical>
**Planning only.** Never apply diffs to source files. The only file you write is the sketch document itself.
</critical>

- **No fabricated context.** Every code snippet must come from a file you Read in this session.
- **Brevity.** Target a 3-6 minute read. Prefer tables and diff blocks over prose. Omit empty sections. If the sketch outgrows this, escalate to `/plan`.
- Keep technical claims precise and verifiable against the code you read.
