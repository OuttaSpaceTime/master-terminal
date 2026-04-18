return {
  {
    "mrjones2014/smart-splits.nvim",
    build = "./kitty/install-kittens.bash",
    init = function()
      vim.g.smart_splits_multiplexer_integration = "kitty"
    end,
    opts = {
      at_edge = "stop",
    },
  },
}
