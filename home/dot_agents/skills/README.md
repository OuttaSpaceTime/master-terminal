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
| /scout | `.claude/docs/scouts/` | `NNN-<name>-YYYYMMDD.md` |
| /plan | `.claude/docs/plans/` | `plan-YYYYMMDD-HHMMSS.md` |
| /review | `.claude/docs/reviews/` | `NNN-<name>-YYYYMMDD.md` |
| /sketch | `.claude/docs/sketches/` | `YYYYMMDD-<topic>.md` |
| /d2 | `.claude/diagrams/` | `<flow-name>.d2` (+ .svg, .png) |
| /walkthrough | none (interactive only) | — |
| /control-flow-trace | none (inline output) | — |
| /strict-diff | none (inline output) | — |

## Chaining

Skills can be chained — the output of one feeds the next:

- `/scout` → `/plan` (plan reads the scout artifact, uses Mode A)
- `/review` → `/walkthrough` (walkthrough reads review findings)
- `/scout` → `/walkthrough` (walkthrough walks through unknowns)
- `/plan` → `/walkthrough` (walkthrough walks through the execution flow)
- `/explore-solutions` → `/walkthrough` (walkthrough on chosen approach)

When chaining, the downstream skill reads the most recent artifact from the upstream skill's directory.
Exception: `/walkthrough` consumes upstream artifacts but produces none itself.

## Skill Categories

**Interactive (checkpoint-based)**: scout, plan, review, walkthrough, diff-review, explore-solutions, control-flow-trace
**Autonomous loop**: autoresearch
**Single-pass**: sketch, d2, strict-diff, research
**Workspace-local orchestration**: dot-manage
