local function goto_open_diffview()
  local views = require("diffview.lib").views
  local tabs = {}
  for _, view in ipairs(views) do
    if view.tabpage and vim.api.nvim_tabpage_is_valid(view.tabpage) then
      tabs[#tabs + 1] = view.tabpage
    end
  end
  if #tabs == 0 then
    vim.notify("No open Diffview", vim.log.levels.INFO)
    return
  end
  local cur = vim.api.nvim_get_current_tabpage()
  local idx
  for i, tab in ipairs(tabs) do
    if tab == cur then
      idx = i
      break
    end
  end
  -- On a diffview: go to the next one. Otherwise: go to the first.
  local target = idx and tabs[(idx % #tabs) + 1] or tabs[1]
  vim.api.nvim_set_current_tabpage(target)
end

return {
  {
    "sindrets/diffview.nvim",
    cmd = { "DiffviewOpen", "DiffviewClose", "DiffviewToggleFiles", "DiffviewFocusFiles", "DiffviewRefresh" },
    keys = {
      { "<leader>gv", "<cmd>DiffviewOpen<cr>", desc = "Git Diffview" },
      -- Close via <cmd> (not `:`) so noice's cmdline popup buffer never flashes
      -- into the tab — typing `:DiffviewClose` triggers E445 (the modified noice
      -- buffer blocks tabclose). See sindrets/diffview.nvim#302.
      { "<leader>gc", "<cmd>DiffviewClose<cr>", desc = "Close Diffview" },
      {
        "<leader>gj",
        goto_open_diffview,
        desc = "Go to open Diffview",
      },
      {
        "gj",
        goto_open_diffview,
        desc = "Go to open Diffview",
      },
      {
        "<leader>gM",
        function()
          local base = "origin/main"
          if vim.fn.systemlist({ "git", "rev-parse", "--verify", "origin/main" })[1] == nil
            or vim.v.shell_error ~= 0
          then
            base = "origin/master"
          end
          vim.cmd("DiffviewOpen " .. base .. "...HEAD")
        end,
        desc = "Git Diffview Since Main",
      },
      { "<leader>gF", "<cmd>DiffviewFocusFiles<cr>", desc = "Git Diffview Files" },
      { "<leader>gt", "<cmd>DiffviewToggleFiles<cr>", desc = "Git Diffview Toggle Files" },
      { "<leader>gV", "<cmd>DiffviewFileHistory %<cr>", desc = "Git File History" },
    },
    opts = {
      enhanced_diff_hl = true,
      use_icons = true,
      view = {
        merge_tool = {
          layout = "diff3_mixed",
        },
      },
    },
  },
}
