---
title: Vendored Skills
tags: [ai-agents, skills, provenance]
created: 2026-07-22
updated: 2026-09-18
---

# Vendored Skills

Skills copied into this repo from external sources, with their origin so they can be re-synced or checked upstream.

## triskweline/skills

Source: https://github.com/triskweline/skills (`skills/<name>/SKILL.md`)

A planning + autonomous-implementation skill set. Upstream defines 9 skills; the two below are vendored here:

- `agree-on-everything` — resolve every implementation decision with the user before any code is written (decision table with numbers/slugs, recommended options, explicit agreement).
- `implement-autonomously` — carry requirements to a tested, self-reviewed implementation. **Vendored copy is simplified**: the upstream version chains 5 more skills (`work-in-branch`, `find-verification-tools`, `full-verification`, `effective-rails-testing`, `self-review`) that we did not vendor, so those calls were stripped.

Not vendored (upstream only): `work-in-branch`, `find-verification-tools`, `full-verification`, `effective-rails-testing`, `self-review`, `build-alone`.

### diff-tour is installed with `npx skills`, not vendored

Since 2026-09-29, `diff-tour` is no longer in `home/`. The `skills` CLI owns it (lock entry in
`~/.agents/.skill-lock.json`):

```bash
npx skills add triskweline/skills -g -s diff-tour -a claude-code codex -y   # install
npx skills update --global diff-tour                                         # update
```

The canonical copy is `~/.agents/skills/diff-tour`. Codex reads it there ("universal"), and Claude Code
gets the symlink `~/.claude/skills/diff-tour -> ../../.agents/skills/diff-tour`. Running
`agent-skills-sync --source claude --apply` would pull it back into `home/`, so exclude it from that sync.

## local-review.nvim

Source: https://github.com/ssundarraj/local-review.nvim (`skills/<name>/SKILL.md`). The plugin
itself is installed as `abelfubu/local-review.nvim` (lazy-lock pin `267d350c`). The vendored
`local-review-preserve/SKILL.md` was byte-compared against both the ssundarraj URL and the installed
abelfubu copy on 2026-09-18 and matched; the other upstream skill files were not compared.

The plugin stores review comments as JSON under
`~/.local/state/nvim/local-review/<sha256(repo_root)>.json` — the filename is the sha256 of the
normalized git toplevel with no trailing newline, so a repo's store is findable without Neovim.

- `local-review-preserve` — read comments without clearing them. **Vendored with one addition**: a
  "Local note" section documenting that the upstream command does not work here (below). Re-syncing
  means re-applying that section.

Not vendored: upstream's `local-review` (the clearing variant). Its `LocalReviewExport` deletes every
comment it reads, which is a bad default when the comments are a review in progress — the preserve
variant plus an explicit `LocalReviewClear` covers the same ground without the data loss.

### The headless commands do not work as documented

Both upstream skills tell the agent to run `nvim --headless '+LocalReviewExport...' +qa`. That command
is registered by the plugin's `setup()`, and `home/private_dot_config/nvim/lua/plugins/local-review.lua`
lazy-loads the plugin on `event = "VeryLazy"`, which fires after `UIEnter`. A headless run has no UI,
so the plugin never loads and nvim exits with `E492: Not an editor command: LocalReviewExportPreserve`.

Two fixes, neither applied as of 2026-09-18:

- add `cmd = { "LocalReviewExport", "LocalReviewExportPreserve", "LocalReviewClear", "LocalReviewList" }`
  to the lazy spec, so the commands load on demand — this makes the upstream skills work verbatim
- or load the plugin explicitly in the headless invocation, which is what both local skills do today
  (`vim.opt.runtimepath:prepend(...)` then `require("local_review").setup({})`)

## Local skills built on vendored ones

- `sketch-diff-tour` (local, not upstream) drives `diff-tour`'s script over a change that does not exist
  yet: it drafts into a throwaway `git worktree` off `HEAD`, runs `difftour.py --setup dirty` inside it,
  and assembles the tour **outside** the worktree so the page outlives its removal. It hard-depends on
  `~/.agents/skills/diff-tour/bin/difftour.py`, which the `npx skills` install still provides; if upstream
  renames the script or its `--setup`/`--assemble` flags, that skill breaks.
  Note that `difftour_html.py` finds `assets/` via `os.path.abspath(__file__)`, which does *not* resolve
  symlinks — so the script must be called at its real path, never through a symlink placed in another
  skill's `bin/`.

- `local-review-check` (local, not upstream) audits a review pass rather than performing one: it reads
  the comments non-destructively via `scripts/read_comments.sh`, maps them onto the hunks of
  `git diff <merge-base>` with `scripts/review_coverage.py`, and reports which hunks carry no comment
  plus a judgement on whether the comments show understanding or just restate the diff. Two details
  are load-bearing: the diff is taken against the **working tree**, not `HEAD`, because comment
  anchors are on-disk line numbers; and hunks are bucketed `source`/`test`/`generated` so a branch
  whose fixtures were regenerated does not report a misleading "13/105 commented".
