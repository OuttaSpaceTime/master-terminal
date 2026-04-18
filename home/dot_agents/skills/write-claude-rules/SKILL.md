---
name: write-claude-rules
description: Use this skill when the user wants to create, write, or improve a CLAUDE.md file, Claude rules, project instructions for Claude Code, or `.claude/rules/` files. Also use when the user asks "how to write good Claude rules", "what should go in CLAUDE.md", "help me set up project memory", "write instructions for Claude", "how to organize rules", "debug rules", or "why aren't my rules working".
version: 1.2.0
---

# Writing Good Claude Rules

## Where to Put Instructions

| Scope | Location | Use for |
|-------|----------|---------|
| Project (shared) | `./CLAUDE.md` or `./.claude/CLAUDE.md` | Team standards, build commands, architecture — checked into git |
| Personal | `~/.claude/CLAUDE.md` | Personal preferences across all projects |
| Topic-specific | `.claude/rules/<topic>.md` | Modular rules, optionally path-scoped |

**Rule of thumb:** team standards → project CLAUDE.md. Personal quirks → user CLAUDE.md. Large/topic-specific → `.claude/rules/`.

**Precedence (highest to lowest):**
1. Path-scoped project rules (`.claude/rules/*.md` with `paths:` frontmatter)
2. Unconditional project CLAUDE.md (root `./CLAUDE.md`)
3. Path-scoped user rules (`~/.claude/rules/*.md` with `paths:` frontmatter)
4. Unconditional user CLAUDE.md (`~/.claude/CLAUDE.md`)

When rules conflict, higher-precedence rules win. Path-scoped rules are the most specific and always take priority.

## Rule File Template

Use this structure for every `.claude/rules/` file:

```markdown
---
paths:
  - "src/api/**/*.ts"
---

# <Rule Title>

## Context
- When this rule applies
- Prerequisites or conditions

## Requirements
- Concise, actionable items
- Each requirement must be testable/verifiable

<example>
  Good concise example with explanation
</example>

<example type="invalid">
  Bad example with explanation of why it fails
</example>

<critical>
  - Rules that must NEVER be violated
  - Absolute constraints
</critical>
```

**Notes:**
- Omit `paths` frontmatter for rules that load unconditionally every session
- `paths` accepts standard glob patterns (no quotes needed)
- Use `<critical>` sparingly — only for true absolutes

## File Naming Convention

Use numbered prefixes in `.claude/rules/`:

| Prefix | Category |
|--------|----------|
| `0XX-` | Core standards (always loaded) |
| `1XX-` | Tool / environment config |
| `3XX-` | Testing standards |
| `8XX-` | Workflows |
| `9XX-` | Templates |
| `_name.md` | Private / draft rules |

Example: `030-code-style.md`, `310-testing.md`, `800-git-workflow.md`

## Writing Effective Instructions

**Specificity is the single most important quality.** Write instructions concrete enough to verify:

| Vague ❌ | Specific ✅ |
|----------|------------|
| "Format code properly" | "Use 2-space indentation, no trailing commas" |
| "Test your changes" | "Run `npm test` before committing" |
| "Keep files organized" | "API handlers live in `src/api/handlers/`" |

**Size:** target under 200 lines per file. Past 200 lines → split into `.claude/rules/` or use `@path` imports.

**Consistency:** conflicting instructions cause unpredictable behavior. Audit across files periodically.

## What Belongs in CLAUDE.md

✅ Include:
- Build / test / lint / dev commands
- Non-obvious architecture (where things live and why)
- Project-specific conventions that differ from community defaults
- Gotchas: env var requirements, known footguns, ordering constraints
- Preferred libraries when multiple options exist

❌ Exclude:
- Things derivable from reading the code
- Generic best practices (Claude already knows these)
- One-off context for a single conversation
- Docs that belong in README

**Concrete mistakes to avoid:**

| Bad rule | Why it fails | Better version |
|----------|-------------|----------------|
| "Run tests frequently and carefully" | Vague, not verifiable | "Run `npm test` before opening PRs; fail if coverage drops below 80%" |
| "Write clean code" | Subjective, no criteria | "Functions max 30 lines; no nested callbacks deeper than 2 levels" |
| "Be careful with the database" | No actionable guidance | "Never run raw SQL outside `src/db/queries/`; always use parameterized queries" |
| "Follow best practices" | Claude already does this | Remove entirely — add only project-specific deviations from defaults |

## CLAUDE.md Template

```markdown
# <Project Name>

<One-line description>

## Commands

| Command | Description |
|---------|-------------|
| `npm run dev` | Start dev server on port 3000 |
| `npm test` | Run all tests (requires local Postgres) |
| `npm run lint` | Lint and autoformat |

## Architecture

​```
src/
  api/        # Express route handlers
  models/     # Database models (Prisma)
  services/   # Business logic
  utils/      # Pure helper functions
​```

## Code Style

- Named exports only, no default exports
- `async/await` over `.then()` chains
- Error types live in `src/errors/`

## Environment

- `DATABASE_URL` — Postgres connection string
- `JWT_SECRET` — Auth token signing key

## Gotchas

- Run `npm run db:migrate` after pulling schema changes
- `src/config/` loads once at startup; changes require restart

## Testing

- Do NOT mock the database in integration tests
```

## Glob Patterns for `paths`

| Pattern | Matches |
|---------|---------|
| `**/*.ts` | All TypeScript files |
| `src/**/*` | All files under `src/` |
| `src/**/*.{ts,tsx}` | TS and TSX anywhere in src |
| `**/*.test.ts` | All test files |
| `src/components/**/*.tsx` | React components only |

## Other Mechanisms

**`@path` imports** — pull in files without duplicating:
```markdown
See @README.md for project overview.
@~/.claude/personal-preferences.md
```

**Path-scoped rules** only load when Claude touches matching files — use them to save context for large rule sets.

## Size and Performance

Large rule sets add context overhead that reduces the effective context window for your actual work.

- **Target 5-10 rule files max** for unconditional rules. Beyond that, context cost grows noticeably.
- **Use `paths:` scoping** to load rules conditionally — a rule scoped to `src/api/**` only consumes context when API files are touched.
- If you find yourself with 15+ rule files all loading unconditionally, consolidate related rules or add path scoping.
- Individual files should stay under 200 lines. If a rule file grows past that, split it.

## Example Project Structure

A monorepo with frontend and backend might organize rules like this:

```
CLAUDE.md                           # Shared: monorepo commands, top-level architecture
.claude/
  rules/
    010-code-style.md               # Shared code style (no paths: → always loaded)
    020-git-workflow.md             # Commit conventions, PR process
    200-api-conventions.md          # paths: ["packages/api/**"]
    210-api-error-handling.md       # paths: ["packages/api/**"]
    300-frontend-components.md      # paths: ["packages/web/**/*.tsx"]
    310-frontend-testing.md         # paths: ["packages/web/**/*.test.tsx"]
    800-deployment.md               # paths: ["infra/**", "Dockerfile*"]
```

Key points:
- Shared rules (010, 020) have no `paths:` — they load every session
- Backend rules (200, 210) only load when touching `packages/api/`
- Frontend rules (300, 310) only load when touching `packages/web/`
- This keeps any single session's context lean

## Common Mistakes

**Rules that contradict settings.json permissions.** Example: a rule says "always run `docker compose up` to verify" but `docker` is not in the allowed commands list. Claude will be blocked by the permission system regardless of the rule. Ensure your settings.json permissions align with what your rules ask Claude to do.

**Rules that assume tool availability.** Example: "use `gh pr create` to open PRs" — but the user may not have `gh` installed, or may be working offline. Add fallback instructions or note prerequisites.

**Overly specific rules that break on minor changes.** Example: "the auth middleware is at `src/middleware/auth.ts` line 42-58" — this breaks the moment that file is edited. Reference functions/exports by name, not line numbers. Prefer "the `authenticateRequest` middleware in `src/middleware/auth.ts`" instead.

**Behavioral rules in settings.json.** Settings.json is for tool permissions, env vars, and hooks only. All behavioral guidance belongs in CLAUDE.md or `.claude/rules/`.

**Duplicating framework defaults.** Example: "use `async/await` in JavaScript" — Claude already does this. Only document deviations from standard practices.

## Debugging Rules

When rules seem to be ignored, work through this decision tree:

**1. Verify which rules are loaded:**
- Run `/memory` in Claude Code to see all loaded instruction sources
- Check if your rule file appears in the list

**2. Check paths glob matching:**
- If the rule has `paths:` frontmatter, it only loads when Claude reads/writes files matching that glob
- Test your glob: does `src/components/Button.tsx` match `src/**/*.tsx`? Yes. Does it match `components/**`? No (missing the `src/` prefix).
- Common mistake: using `*.ts` (root only) when you meant `**/*.ts` (recursive)

**3. Check for conflicts:**
- Two rules giving opposite instructions → unpredictable behavior
- Search across all rule files for contradictions: `grep -r "keyword" .claude/rules/`
- Higher-precedence rules override lower ones (see Precedence above)

**4. Check specificity:**
- "Format code properly" is too vague to act on — make it specific and verifiable
- If a rule is consistently ignored, it may be too abstract for Claude to operationalize

**5. Check rule file format:**
- File must be `.md` extension in `.claude/rules/`
- `paths:` frontmatter must be valid YAML between `---` fences
- File must be saved (not just open in editor)

## After Writing

- Run `/memory` to verify the file is loaded in the current session.
- Conflicting rules? More specific location wins; project rules beat user rules.
- Instructions ignored? Make them more specific, check for contradictions.

<critical>
  - NEVER put behavioral guidance in settings.json — that's for tool permissions and env vars only
  - NEVER use verbose explanations in rules; high information density, minimal tokens
  - Keep each rule file focused on ONE topic
</critical>
