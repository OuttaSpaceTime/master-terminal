# Repository Guidelines

## Purpose

This repository has three responsibilities:

- a chezmoi source tree for terminal and editor configuration under `home/`
- a minimal local wiki for repo-specific workflow lookup under `wiki/`
- a workspace-local agent skill tree under `home/dot_agents/skills/`

## Project Structure

- `README.md` stays minimal and only identifies the repo and its roles
- `AGENTS.md` is the operating schema for the repo
- `home/` is the chezmoi source tree
- `home/dot_agents/skills/` is the workspace-local skill source tree for this repository
- `wiki/` contains the maintained local lookup notes for this repo only

## Ownership Rules

- `home/` remains operational dotfiles and skill sources only
- `wiki/` is a small local memory for repo-specific answers the user actually asked for
- keep the repo root sparse
- do not mix wiki content into `home/`
- do not reintroduce `raw/`, `wiki/sources/`, `wiki/reflections/`, or `wiki/evals/` here
- `~/Code/Misc/wiki` may receive moved general notes or reflections, but this repo must never read from it as part of its workflow

## Working With Chezmoi

**Cardinal rule: only edit source files under `home/`. Never edit deployed files (e.g. `~/.config/`, `~/.agents/`) directly.** All changes flow one way: edit chezmoi source → diff → apply.

- Use a global `chezmoi` installation from the repo root
- The source paths map through chezmoi, for example:
  - `home/private_dot_config/nvim/init.lua` -> `~/.config/nvim/init.lua`
  - `home/private_dot_config/kitty/kitty.conf` -> `~/.config/kitty/kitty.conf`
  - `home/dot_agents/skills/scout/SKILL.md` -> `~/.agents/skills/scout/SKILL.md`

### Modification workflow

1. **Before editing**, run `chezmoi -S home diff` to check for conflicts — deployed files may have been modified outside chezmoi. Review any drift before overwriting it.
2. Edit only source files under `home/`
3. Run `chezmoi -S home diff` again to preview the changes that will be deployed
4. Run `chezmoi -S home apply` to deploy (add `--force` if drift was reviewed and is safe to overwrite)

**`~/.claude/settings.json` does not drift.** Its chezmoi source is a `modify_` script (`home/dot_claude/modify_settings.json`), not a plain file: chezmoi feeds it the deployed file on stdin and uses its stdout as the target contents. Keys you toggle in the UI (`model`, `outputStyle`, `effortLevel`, `theme`, …) are passed straight through from the live file, so `chezmoi -S home diff` stays empty; `permissions`, `hooks`, `statusLine` and `enabledPlugins` are still enforced from the repo. Edit the `MANAGED` blob to change those — `DEFAULTS` only seeds a machine that lacks the key. Details in `wiki/claude-code.md`.

## Working With Agent Skills

- Agent skills are chezmoi-managed. Edit only the source files under `home/dot_agents/skills/`, then deploy with `chezmoi -S home apply`
- Never edit deployed skill files under `~/.agents/skills/` directly — chezmoi owns those targets
- Treat `dot-manage` as the workspace-local orchestration skill for repo-specific dotfile, skill, and wiki adjustments
- When a request touches tools, settings, plugins, keymaps, shells, or workspace skills, inspect the relevant `home/` files directly
- Keep durable repo-specific workflow knowledge in the local `wiki/`
- Do not use a separate repo-local `.agents/skills/wiki-*` layer in this repository
- Skills that are no longer in regular use can be archived with `agent-skills-archive <name>` — the source is moved to `home/dot_agents/skills-archive/` and the Claude/Codex symlinks plus deployed copies are removed. Restore with `agent-skills-archive --restore <name>`. Archived skills are preserved in the repo, just not deployed.
- **`home/dot_agents/skills-archive/` is preserved-but-inactive: never edit a skill there.** Nothing under it deploys, so editing it has no live effect and the content must stay a faithful snapshot of when it was archived. If an archived skill needs changes, restore it first (`agent-skills-archive --restore <name>`), edit the now-active source under `home/dot_agents/skills/`, then re-archive if desired. A `PreToolUse` hook (`.claude/hooks/no-edit-archive.py`) blocks `Edit`/`Write`/`MultiEdit` on `skills-archive/` paths to enforce this.

## Working With The Local Wiki

- `wiki/` is a flat directory — one file per topic, no subdirectories
- `wiki/index.md` is the content catalog and starting point
- Each topic file has YAML frontmatter with `title`, `tags`, `created`, `updated`
- Use kebab-case filenames
- Update existing pages before creating near-duplicates
- Keep updates minimal and tied to what the user actually asked or what the current task proved

## Query Workflow

1. Read `wiki/index.md` for existing topics
2. Grep `wiki/` for keywords when the index isn't enough
3. Inspect `home/`, repo files, and workspace skills directly when the answer depends on current configuration
4. If the answer is still missing, research the web
5. Persist the smallest update that makes the answer rediscoverable — extend an existing topic file or create a new one
6. Update `wiki/index.md` when a file is added or removed

## Commands

```bash
# Preview what chezmoi will change before deploying
chezmoi -S home diff

# Deploy all managed files
chezmoi -S home apply

# Force deploy (when drift was reviewed and is safe to overwrite)
chezmoi -S home apply --force

# Deploy only skills
chezmoi -S home apply --force ~/.agents/skills ~/.claude/skills ~/.codex/skills

# Archive a rarely-used skill (move source out of deployment path)
agent-skills-archive <name> [<name> ...]
agent-skills-archive --list
agent-skills-archive --restore <name>

# Import skills from deployed ~/.claude/skills back into chezmoi source tree
agent-skills-sync --source claude --apply
agent-skills-sync --source claude --dry-run   # preview first
agent-skills-sync --skill <name> --apply      # single skill

# Apply GNOME keyboard shortcuts from config
apply-gnome-shortcuts
```

## Architecture

### Skill deployment chain

Skills have a three-layer deployment via chezmoi:

1. **Canonical source:** `home/dot_agents/skills/<name>/SKILL.md` — the actual skill content lives here
2. **Agent symlinks:** `home/dot_claude/skills/symlink_<name>` and `home/dot_codex/skills/symlink_<name>` — each contains `../../.agents/skills/<name>`, making chezmoi create symlinks at deploy time
3. **Deployed result:** `~/.claude/skills/<name>` → `~/.agents/skills/<name>` (symlink to shared location)

This means all three agent runtimes (agents, claude, codex) share identical skill content from a single source. When adding a new skill, you must create both symlink files in addition to the skill directory.

### Shared skill references

Shared reference files (e.g. `interactive-principles.md`, `parallel-agents.md`) live in `home/dot_agents/skills/references/` as a single source of truth. Skills must **never** use `../references/` paths to reach them — agents loading a skill cannot resolve relative paths that escape the skill directory.

Instead, each skill that needs a shared reference gets a chezmoi symlink file in its own `references/` subdirectory:

1. Create `home/dot_agents/skills/<skill>/references/symlink_<name>.md` with content `../../references/<name>.md`
2. Chezmoi deploys this as a symlink: `~/.agents/skills/<skill>/references/<name>.md` → `../../references/<name>.md`
3. The SKILL.md references it as `references/<name>.md` — a simple path relative to the skill folder

This way the agent sees `references/interactive-principles.md` as a local file within the skill's directory tree and can read it directly. The symlink resolves to the shared canonical copy, so there is still only one source of truth.

**When adding a new shared reference or when a skill newly needs an existing one:**
- Add the canonical file to `home/dot_agents/skills/references/` (if new)
- Create a `symlink_<name>.md` file in each consuming skill's `references/` directory
- Reference it as `references/<name>.md` in the SKILL.md (no `../`, no absolute paths)

### agent-skills-sync

`home/dot_local/bin/executable_agent-skills-sync` is a Python script that does the reverse: imports skills from a deployed agent directory (e.g. `~/.claude/skills/`) back into the chezmoi source tree at `home/dot_agents/skills/`. It normalizes frontmatter, rewrites hardcoded paths to portable relative paths, and generates `agents/openai.yaml` metadata for Codex compatibility.

### Neovim

The nvim config under `home/private_dot_config/nvim/` is a LazyVim distribution. Custom plugins go in `lua/plugins/`, and user config overrides go in `lua/config/` (keymaps, options, autocmds, lazy bootstrap).

### Chezmoi naming conventions

Chezmoi source filenames encode target attributes:
- `private_dot_config/` → `~/.config/` (private permissions)
- `dot_zshrc` → `~/.zshrc`
- `dot_agents/` → `~/.agents/`
- `executable_` prefix → file gets +x after deploy
- `symlink_` prefix → chezmoi creates a symlink whose target is the file's content

### SolveIt hooks

The SolveIt PreToolUse guards live under `home/dot_claude/solveit/hooks/` and deploy via chezmoi to `~/.claude/solveit/hooks/`. We work on these frequently.

- `executable_bash-guard.py` — allows Bash only for task scripts + read-only search/git inspection; blocks everything else, including Claude running `current.<ext>` (only the human runs it, with `!`) (command recognition lives in `segment_ok`/`split_segments`)
- `executable_edit-guard.py` — enforces the 30-line-per-edit ceiling (`CAP`), 1 project edit per turn (`EDIT_CAP`, the one-step-per-turn rhythm), the dirty (30) / warn (150) / hard (300) uncommitted caps, and holds a *new* `current.<ext>` (project edits and in-place fixes still land) until the human has `!`-run the one written before their last prompt (`unrun_current`, read from the transcript)
- `executable_stop-affordance-guard.py` — turn-level rules: prose length, no trailing menus, no asking the human to paste output, hedging on read-only turns, single-line commands
- `executable_log-reads.py` — mirrors Read/Grep/Glob into `.solve/reads.log`
- `executable_solve-init.py` — session bootstrap; resets the per-turn edit counter
- `solve_allow.py` — shared allowlist reader for bash-guard + solve-init, plus `log_guard_error()` (all guards fail open but append to `~/.claude/solveit/guard-errors.log`)

`solveit-health` (`home/dot_local/bin/executable_solveit-health` + the `solveit-health` skill) scores recent transcripts against these rules and proposes allowlist entries — run it after changing a hook.

Tests live in `tests/` (pytest, `uv run pytest`). The `executable_`/hyphen source names aren't importable normally — load a hook in a test via `importlib.util.spec_from_file_location` from its source path.

## Validation

- There is no application build or test pipeline in this repository snapshot
- Validate wiki edits by checking structure, links, and note consistency
- Validate `home/` changes with `chezmoi -S home diff` when relevant
