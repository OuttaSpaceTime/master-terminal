return {
  {
    "mikesmithgh/kitty-scrollback.nvim",
    cmd = {
      "KittyScrollbackGenerateKittens",
      "KittyScrollbackCheckHealth",
      "KittyScrollbackGenerateCommandLineEditing",
    },
    event = { "User KittyScrollbackLaunch" },
    config = function()
      require("kitty-scrollback").setup({
        ksb_builtin_get_text_all = {
          paste_window = {
            yank_register_enabled = false,
          },
        },
      })
    end,
  },
}
