return {
  {
    "neovim/nvim-lspconfig",
    opts = {
      servers = {
        ruby_lsp = {
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
            },
          },
          capabilities = {
            general = {
              positionEncodings = { "utf-16" },
            },
          },
        },
        solargraph = {
          cmd = { "rbenv", "exec", "solargraph", "stdio" },
        },
        rubocop = {
          cmd = { "rbenv", "exec", "rubocop", "--lsp" },
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
