return {
  {
    "sindrets/diffview.nvim",
    cmd = { "DiffviewOpen", "DiffviewClose", "DiffviewToggleFiles", "DiffviewFocusFiles", "DiffviewRefresh" },
    keys = {
      { "<leader>gv", "<cmd>DiffviewOpen<cr>", desc = "Git Diffview" },
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
