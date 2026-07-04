return {
  {
    "neovim/nvim-lspconfig",
    opts = {
      servers = {
        rubocop = { enabled = false },
        ruby_lsp = {
          mason = false,
          cmd = { "rbenv", "exec", "ruby-lsp" },
          -- When opening a file inside an installed gem, attach to the project's
          -- already-running ruby-lsp client (which has the whole bundle indexed)
          -- instead of spawning a new server rooted at the gem dir or ~/.rbenv.
          -- Without this, go-to-definition/hover stop working once inside gem code.
          root_dir = function(bufnr, on_dir)
            local fname = vim.api.nvim_buf_get_name(bufnr)
            if fname:match("/gems/[^/]+/") then
              local clients = vim.lsp.get_clients({ name = "ruby_lsp" })
              if clients[1] and clients[1].config.root_dir then
                return on_dir(clients[1].config.root_dir)
              end
            end
            on_dir(vim.fs.root(bufnr, { "Gemfile", ".git" }) or vim.fn.getcwd())
          end,
          init_options = {
            -- "auto" lets ruby-lsp detect rubocop vs. standard per project from
            -- the bundle, instead of forcing rubocop everywhere.
            formatter = "auto",
            linters = { "rubocop" },
            -- Inlay hints are listed in enabledFeatures, but ruby-lsp only emits
            -- the hint content when these are turned on.
            featuresConfiguration = {
              inlayHint = {
                implicitHashValue = true, -- { name: } -> { name: name }
                implicitRescue = true, -- bare `rescue` -> StandardError
              },
            },
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
  {
    "stevearc/conform.nvim",
    opts = function(_, opts)
      opts.formatters_by_ft = opts.formatters_by_ft or {}
      opts.formatters_by_ft.ruby = nil
      return opts
    end,
  },
}
