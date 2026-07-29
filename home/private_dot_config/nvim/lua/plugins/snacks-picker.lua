return {
  {
    "folke/snacks.nvim",
    opts = {
      picker = {
        layouts = {
          default = { layout = { backdrop = false } },
        },
        sources = {
          explorer = {
            include = { ".solve", ".solve/**" },
          },
        },
      },
    },
  },
}
