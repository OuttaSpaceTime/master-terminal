return {
  {
    "neovim/nvim-lspconfig",
    opts = {
      servers = {
        vtsls = {
          filetypes = {
            "javascript",
            "javascriptreact",
            "typescript",
            "typescriptreact",
          },
        },
      },
    },
  },
  {
    "windwp/nvim-ts-autotag",
    opts = function(_, opts)
      opts = opts or {}
      opts.aliases = opts.aliases or {}
      opts.aliases["javascriptreact"] = "typescriptreact"
      opts.aliases["typescriptreact"] = "typescriptreact"
      opts.aliases["javascript"] = "typescriptreact"
      opts.aliases["typescript"] = "typescriptreact"
      opts.aliases["javascript.jsx"] = nil
      opts.aliases["typescript.tsx"] = nil
    end,
  },
}
