return {
  {
    "neovim/nvim-lspconfig",
    opts = {
      servers = {
        ruby_lsp = {
          mason = false,
          cmd = { "rbenv", "exec", "ruby-lsp" },
          init_options = {
            formatter = "rubocop",
            linters = { "rubocop" },
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
      },
    },
  },
}
