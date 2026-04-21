return {
  {
    "neovim/nvim-lspconfig",
    opts = {
      servers = {
        ruby_lsp = {
          mason = false,
          cmd = { "rbenv", "exec", "ruby-lsp" },
          init_options = {
            enabledFeatures = {
              "documentHighlights",
              "documentSymbols",
              "foldingRanges",
              "selectionRanges",
              "semanticHighlighting",
              "formatting",
              "codeActions",
              "diagnostics",
              "completion",
              "codeLens",
              "definition",
              "hover",
              "signatureHelp",
              "workspaceSymbol",
              "inlayHint",
              "references",
            },
          },
          capabilities = {
            general = {
              positionEncodings = { "utf-16" },
            },
          },
        },
        rubocop = {
          mason = false,
          cmd = { "rbenv", "exec", "bundle", "exec", "rubocop", "--lsp", "--no-server" },
          capabilities = {
            general = {
              positionEncodings = { "utf-16" },
            },
          },
        },
      },
    },
  },
}
