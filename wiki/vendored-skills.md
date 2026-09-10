---
title: Vendored Skills
tags: [ai-agents, skills, provenance]
created: 2026-07-22
updated: 2026-09-10
---

# Vendored Skills

Skills copied into this repo from external sources, with their origin so they can be re-synced or checked upstream.

## triskweline/skills

Source: https://github.com/triskweline/skills (`skills/<name>/SKILL.md`)

A planning + autonomous-implementation skill set. Upstream defines 9 skills; the three below are vendored here:

- `agree-on-everything` — resolve every implementation decision with the user before any code is written (decision table with numbers/slugs, recommended options, explicit agreement).
- `diff-tour` — narrated HTML walkthrough of a diff you did not write: hunks clustered into themed chapters in a reading order, each beside prose, each carrying a heat level. **Vendored whole**, including `bin/difftour.py`, `bin/difftour_html.py`, `assets/`, `tests/` and the 52-file `vendor/prism/` bundle — the script resolves `assets/` and `vendor/prism/` relative to the skill directory, so those three must stay siblings of `bin/`. Pinned at upstream `e59d677`. Upstream's `bin/difftour.py` is `executable_difftour.py` in the chezmoi source; nothing else was renamed or edited.
- `implement-autonomously` — carry requirements to a tested, self-reviewed implementation. **Vendored copy is simplified**: the upstream version chains 5 more skills (`work-in-branch`, `find-verification-tools`, `full-verification`, `effective-rails-testing`, `self-review`) that we did not vendor, so those calls were stripped.

Not vendored (upstream only): `work-in-branch`, `find-verification-tools`, `full-verification`, `effective-rails-testing`, `self-review`, `build-alone`.

### Re-syncing diff-tour

```bash
git clone --depth 1 https://github.com/triskweline/skills.git /tmp/tris
rsync -a --delete /tmp/tris/skills/diff-tour/ home/dot_agents/skills/diff-tour/
mv home/dot_agents/skills/diff-tour/bin/difftour.py home/dot_agents/skills/diff-tour/bin/executable_difftour.py
chezmoi -S home diff && chezmoi -S home apply
uv run pytest ~/.agents/skills/diff-tour/tests/test_difftour.py -q
```

The vendored tests do not join this repo's suite: `pyproject.toml` sets `testpaths = ["tests"]`, so they
only run when pointed at explicitly, as above. Last verified 2026-09-10: 37 passed.

## Local skills built on vendored ones

- `sketch-diff-tour` (local, not upstream) drives `diff-tour`'s script over a change that does not exist
  yet: it drafts into a throwaway `git worktree` off `HEAD`, runs `difftour.py --setup dirty` inside it,
  and assembles the tour **outside** the worktree so the page outlives its removal. It hard-depends on
  `~/.agents/skills/diff-tour/bin/difftour.py`; if `diff-tour` is ever unvendored, that skill breaks.
  Note that `difftour_html.py` finds `assets/` via `os.path.abspath(__file__)`, which does *not* resolve
  symlinks — so the script must be called at its real path, never through a symlink placed in another
  skill's `bin/`.
