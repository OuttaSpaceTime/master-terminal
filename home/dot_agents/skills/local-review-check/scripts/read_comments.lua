-- Emit every local-review.nvim comment for the current repo as JSON on stdout.
-- Read-only: goes through list_comments_in_path, which never clears the store.
local plugin_dir = os.getenv("LOCAL_REVIEW_PLUGIN_DIR")
if plugin_dir == nil or plugin_dir == "" then
  plugin_dir = vim.fn.expand("~/.local/share/nvim/lazy/local-review.nvim")
end
vim.opt.runtimepath:prepend(plugin_dir)

require("local_review").setup({})

local ctx = require("local_review.infrastructure.context")
local app = require("local_review.application.comments")

local list = app.list_comments_in_path(ctx.default_export_root()) or {}
local out = {}
for _, c in ipairs(list) do
  out[#out + 1] = {
    path = c.relative_path or c.absolute_path,
    line = c.anchor.line_number,
    line_end = c.line_end or c.anchor.line_number,
    body = c.body,
    stale = c.stale and true or false,
    origin = c.origin,
  }
end

io.write(vim.json.encode(out))
