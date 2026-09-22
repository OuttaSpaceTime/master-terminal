#!/usr/bin/env bash
# Emit local-review.nvim comments for the current repo as JSON, without deleting them.
#
# The documented `nvim --headless '+LocalReviewExportPreserve' +qa` only works when the
# plugin is already loaded. Under lazy.nvim with `event = "VeryLazy"` it never loads in a
# headless run (VeryLazy fires after UIEnter, and there is no UI), so the command is not
# registered and nvim exits with E492. Loading the plugin explicitly sidesteps that and is
# independent of how the user's config chooses to lazy-load it.
set -euo pipefail

here=$(dirname "$(readlink -f "$0")")

nvim --headless -u NONE -n \
  -c "luafile $here/read_comments.lua" \
  -c qa
