# Shared Agent Skills — Cross-Skill Conventions

This tree is the chezmoi-managed source for reusable personal skills and workspace-local skills used from this repository.

- Canonical location: `$HOME/.agents/skills`
- Claude compatibility: `~/.claude/skills` symlinked into the shared tree
- Codex compatibility: `~/.codex/skills` symlinked into the shared tree
- Import/update workflow:
  - `agent-skills-sync --dry-run`
  - `agent-skills-sync --apply`

## Workspace-Local Skills

- Some skills in this tree are intentionally workspace-specific and should only document behavior for this repository
- `dot-manage` is the workspace-local skill for repo-specific dotfile changes, workspace skill changes, and minimal local wiki maintenance
- Repo-local wiki behavior is defined directly in `AGENTS.md` and routed through `dot-manage`, not through a separate repo-local wiki skill subsystem

Example: sync a Claude skill into the shared tree from the repo root:

```bash
agent-skills-sync --source claude --skill plan --dry-run
agent-skills-sync --source claude --skill plan --apply
```

## Artifact Locations

All skills that produce artifacts write to `.claude/` relative to the project root:

| Skill | Artifact Path | Naming Pattern |
|-------|--------------|----------------|
| /sketch | `.claude/docs/sketches/` | `YYYYMMDD-<topic>.md` |
| /diff-tour | system temp or `tmp/` | `diff-tour.<rand>/diff-tour.html` |
| /sketch-diff-tour | system temp | `sketch-tour.<rand>/sketch-tour.html` |
| /walkthrough | none (interactive only) | — |

## Chaining

Skills can be chained — the output of one feeds the next:

- `/explore-solutions` → `/walkthrough` (walkthrough on chosen approach)
- `/sketch` → `/sketch-diff-tour` (the sketch's file list and decisions seed the draft)
- `/explore-solutions` → `/sketch-diff-tour` (one worktree and one tour per candidate approach)
- `/sketch-diff-tour` → `/diff-tour` (same page, once the change is really built)
- `/shape-code` → `/trim-code` (where code lives first, then how much of it; trimming first can delete evidence for a move)

When chaining, the downstream skill reads the most recent artifact from the upstream skill's directory.
Exception: `/walkthrough` consumes upstream artifacts but produces none itself.

## Skill Categories

**Interactive (checkpoint-based)**: walkthrough, explore-solutions, shape-code
**Single-pass**: sketch, diff-tour, sketch-diff-tour
**Workspace-local orchestration**: dot-manage
