return {
  {
    "abelfubu/local-review.nvim",
    event = "VeryLazy",
    keys = {
      { "<leader>re", "<cmd>LocalReviewExportPreserve<cr>", desc = "Export Review Comments (keep)" },
    },
    opts = {
      keymaps = {
        comment = "<leader>rc",
        delete = "<leader>rd",
        next = "]r",
        prev = "[r",
        export = false,
        list = "<leader>rl",
        hover = "K",
      },
      comment_close_keys = {
        { modes = { "n" }, key = "q" },
        { modes = { "n", "i" }, key = "<C-c>" },
      },
    },
  },
  {
    "folke/which-key.nvim",
    opts = {
      spec = {
        { "<leader>r", group = "review" },
      },
    },
  },
}
