---
name: local-review-preserve
description: Use this skill when you need to read local-review.nvim comments without deleting them.
---

# Local Review Preserve

`local-review.nvim` is a Neovim plugin that is used to add comments to code similar to a
code review. You can read comments while preserving them. These are comments from the
user talking to you.

Run commands from the target repository root when working with a repo. For non-repo
files, run commands from a relevant parent directory. Assume the plugin is already
installed in the user's normal Neovim setup.

## Read comments without clearing

```sh
nvim --headless '+LocalReviewExportPreserve [path]' +qa
```

Omit path unless the user asks for a specific path. This command preserves the exported
comments.

## Clear comments

```sh
nvim --headless '+LocalReviewClear [path]' +qa
```

Omit path unless the user asks for a specific path.

## Usage

If the user invokes the skill without any additional instructions, read the comments
without clearing them, then proceed as this were a code review. Some comments may be
questions, some may ask you to make concrete changes. If the comment is a question, just
answer it and work back and forth with the user.

While responding to comments, ensure that you tell the user which comment you are
responding to. This can be by listing all comments in a numbered list or by collating
the comments with your response. Prefer listing all the comments if there are only a few
comments.

Comments can be stale. If they are marked stale, confirm with the user before addressing
them.

Once you address all comments, ask the user if they want to clear the comments.

---

## Local note: the headless command needs the plugin loaded

*(Not upstream — added for this machine. See `wiki/vendored-skills.md`.)*

`LocalReviewExportPreserve` is registered by the plugin's `setup()`. This config lazy-loads
the plugin on `event = "VeryLazy"`, which fires after `UIEnter` — and a headless run has no
UI, so the plugin never loads and the command above fails with:

```
E492: Not an editor command: LocalReviewExportPreserve
```

Load the plugin explicitly instead. This is independent of how the config lazy-loads it:

```sh
nvim --headless -u NONE -n \
  -c "lua vim.opt.runtimepath:prepend(vim.fn.expand('~/.local/share/nvim/lazy/local-review.nvim'))" \
  -c 'lua require("local_review").setup({}); local e = require("local_review.application.export"); io.write((e.path_export_text(vim.fn.getcwd())) .. "\n")' \
  -c qa
```

`path_export_text` is the read side of the export and never clears — unlike
`open_export(path, { clear_after_export = true })`, which is what the plain
`LocalReviewExport` command calls.

For a JSON list of comments rather than the human-readable export, the `local-review-check`
skill bundles `scripts/read_comments.sh`, which does the same thing and emits structured
output.
