---
title: Git Hooks
tags: [git, hooks, rubocop]
created: 2026-05-07
updated: 2026-05-07
---

# Git Hooks

## RuboCop version drift

`~/.githooks/pre-commit` is not currently chezmoi-managed, but the global `~/.gitconfig` sets:

```ini
[core]
  hooksPath = /home/felix/.githooks
```

Some repos can override this with their own `core.hooksPath`. Vilocify portal currently points at `/home/felix/Code/Vilocify/vilocify-portal/.git/hooks`, so `gp` runs that repo-local `pre-push` hook instead of the global hook.

Use `bundle exec rubocop --no-server ...` in hooks. `bundle exec` selects the bundled gems, but RuboCop's server is keyed by project directory and can reuse an already-running unbundled/global server for that same project. In the Vilocify case, the bundle had `rubocop 1.84.2` and `rubocop-rails 2.32.0`, while the global environment had `rubocop 1.86.1` and `rubocop-rails 2.34.3`; the stale server exposed newer cops such as `Rails/HttpStatusNameConsistency`.

This was verified by starting an unbundled server in the Vilocify worktree: `bundle exec rubocop ...` reported the newer global offenses, while `bundle exec rubocop --no-server ...` reported no offenses for the same files.

Neovim can start RuboCop-related processes. The managed config now lets Ruby LSP own RuboCop with `formatter = "rubocop"` and `linters = { "rubocop" }`, which keeps the editor path on the bundled project version without a separate RuboCop LSP client.
