---
name: port-claude-skill-to-codex
description: Port a Claude Code skill into the shared cross-agent skill tree used by chezmoi, rewrite the small set of path assumptions that break portability, and refresh Codex-facing metadata. Use when a Claude-first skill changed and the shared canonical copy in `$HOME/.agents/skills` needs to be imported, normalized, and exposed to both Claude and Codex.
---

# Port Claude Skill To Codex

Use this skill when a reusable skill currently lives in `~/.claude/skills/<name>` and needs to become or remain a shared skill in `$HOME/.agents/skills/<name>`.

## Workflow

1. Inspect the source skill under `~/.claude/skills/<name>`.
2. Classify files:
   - portable: `SKILL.md`, `scripts/`, `references/`, `assets/`, `agents/`
   - non-portable: `*-workspace/`, transient eval runs, caches, and scratch artifacts
3. Run a dry run first:

```bash
agent-skills-sync --source claude --skill <name> --dry-run
```

Example:

```bash
agent-skills-sync --source claude --skill plan --dry-run
agent-skills-sync --source claude --skill plan --apply
```

4. If the planned copy looks correct, apply it:

```bash
agent-skills-sync --source claude --skill <name> --apply
```

5. Verify the imported shared skill:
   - `SKILL.md` frontmatter still has `name` and `description`
   - Codex metadata exists at `agents/openai.yaml`
   - any hard-coded `~/.claude/skills/...` paths were rewritten to shared relative paths
6. Confirm Claude compatibility through the managed symlink at `~/.claude/skills/<name>`.

## Output Requirements

- State which files were imported.
- Call out any skipped non-portable folders.
- Mention whether `agents/openai.yaml` was generated or refreshed.
- Report any remaining Claude-specific assumptions that still need manual cleanup.

## Guardrails

- Do not import `*-workspace` directories into the shared tree.
- Do not silently keep absolute `~/.claude/skills/...` paths when a relative shared path is available.
- Prefer deterministic sync behavior over stylistic rewrites.
