return {
  "lewis6991/gitsigns.nvim",
  opts = function(_, opts)
    local lazyvim_on_attach = opts.on_attach
    opts.on_attach = function(buffer)
      lazyvim_on_attach(buffer)
      local gs = package.loaded.gitsigns
      vim.keymap.set("n", "]h", function()
        if vim.wo.diff then
          vim.cmd.normal({ "]c", bang = true })
        else
          gs.nav_hunk("next", { target = "all" })
        end
      end, { buffer = buffer, desc = "Next Hunk (staged or unstaged)", silent = true })
      vim.keymap.set("n", "[h", function()
        if vim.wo.diff then
          vim.cmd.normal({ "[c", bang = true })
        else
          gs.nav_hunk("prev", { target = "all" })
        end
      end, { buffer = buffer, desc = "Prev Hunk (staged or unstaged)", silent = true })
    end
  end,
}
