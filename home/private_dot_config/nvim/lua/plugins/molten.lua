return {
  {
    "benlubas/molten-nvim",
    version = "^1.0.0",
    build = ":UpdateRemotePlugins",
    dependencies = { "3rd/image.nvim" },
    init = function()
      vim.g.molten_image_provider = "image.nvim"
      vim.g.molten_output_win_max_height = 20
      vim.g.molten_auto_open_output = false
      vim.g.molten_wrap_output = true
      vim.g.molten_virt_text_output = true
      vim.g.molten_virt_lines_off_by_1 = true
    end,
    keys = {
      { "<leader>mi", ":MoltenInit<CR>",                               desc = "Molten Init" },
      { "<leader>me", ":MoltenEvaluateOperator<CR>",                   desc = "Molten Evaluate Operator" },
      { "<leader>ml", ":MoltenEvaluateLine<CR>",                       desc = "Molten Evaluate Line" },
      { "<leader>mc", ":MoltenReevaluateCell<CR>",                     desc = "Molten Reevaluate Cell" },
      { "<leader>mv", ":<C-u>MoltenEvaluateVisual<CR>gv",              desc = "Molten Evaluate Visual", mode = "v" },
      { "<leader>mo", ":MoltenOpenOutputWindow<CR>",                   desc = "Molten Open Output" },
      { "<leader>mh", ":MoltenHideOutput<CR>",                         desc = "Molten Hide Output" },
      { "<leader>md", ":MoltenDelete<CR>",                             desc = "Molten Delete Cell" },
      { "<leader>mq", ":MoltenInterrupt<CR>",                          desc = "Molten Interrupt" },
    },
  },
  {
    "3rd/image.nvim",
    opts = {
      backend = "kitty",
      max_width = 100,
      max_height = 12,
      max_height_window_percentage = math.huge,
      max_width_window_percentage = math.huge,
      window_overlap_clear_enabled = true,
      window_overlap_clear_ft_ignore = { "cmp_menu", "cmp_docs", "" },
    },
  },
  {
    "GCBallesteros/jupytext.nvim",
    opts = {
      style = "markdown",
      output_extension = "md",
      force_ft = "markdown",
    },
  },
  {
    "MeanderingProgrammer/render-markdown.nvim",
    dependencies = { "nvim-treesitter/nvim-treesitter", "nvim-tree/nvim-web-devicons" },
    ft = { "markdown" },
    opts = {
      heading = { enabled = true },
      code = { enabled = true, style = "full" },
      bullet = { enabled = true },
      checkbox = { enabled = true },
    },
  },
  {
    "GCBallesteros/NotebookNavigator.nvim",
    dependencies = {
      "nvim-mini/mini.comment",
      "benlubas/molten-nvim",
      "anuvyklack/hydra.nvim",
    },
    opts = {
      cell_markers = { "```python", "```" },
      activate_hydra_keys = "<leader>mn",
      show_hydra_hint = true,
      hydra_keys = {
        comment = "c",
        run = "X",
        run_and_move = "x",
        move_up = "k",
        move_down = "j",
        add_cell_before = "a",
        add_cell_after = "b",
      },
    },
    keys = {
      { "]c", function() require("notebook-navigator").move_cell("d") end, desc = "Next cell" },
      { "[c", function() require("notebook-navigator").move_cell("u") end, desc = "Prev cell" },
      { "<leader>mX", function() require("notebook-navigator").run_cell() end, desc = "Run cell" },
      { "<leader>mx", function() require("notebook-navigator").run_and_move() end, desc = "Run cell and move" },
    },
  },
}
