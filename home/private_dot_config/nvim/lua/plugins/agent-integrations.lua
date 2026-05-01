return {
  {
    "coder/claudecode.nvim",
    dependencies = { "folke/snacks.nvim" },
    opts = {
      terminal = {
        -- Keep Claude Code in an external kitty/terminal session. The plugin
        -- still starts the IDE server and exposes selection/diff tools.
        provider = "none",
      },
    },
    keys = {
      { "<leader>a", nil, desc = "AI/Agent" },
      { "<leader>ab", "<cmd>ClaudeCodeAdd %<cr>", desc = "Add Buffer to Claude" },
      { "<leader>as", "<cmd>ClaudeCodeSend<cr>", mode = "v", desc = "Send Selection to Claude" },
      { "<leader>aa", "<cmd>ClaudeCodeDiffAccept<cr>", desc = "Accept Claude Diff" },
      { "<leader>ad", "<cmd>ClaudeCodeDiffDeny<cr>", desc = "Deny Claude Diff" },
    },
  },
  {
    "linw1995/nvim-mcp",
    lazy = true,
    enabled = vim.fn.executable("cargo") == 1,
    build = "cargo install --path .",
    opts = function()
      return {
        -- When nvim-listen starts Nvim with a discoverable socket, reuse it
        -- instead of letting the plugin create a second nvim-mcp.<pid>.sock.
        pipe = vim.env.NVIM_LISTEN_ADDRESS,
      }
    end,
  },
}
