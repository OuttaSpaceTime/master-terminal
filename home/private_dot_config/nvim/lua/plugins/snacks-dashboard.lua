return {
  {
    "folke/snacks.nvim",
    opts = function(_, opts)
      opts.dashboard = opts.dashboard or {}
      opts.dashboard.preset = opts.dashboard.preset or {}

      local cwd = vim.fn.fnamemodify(vim.fn.getcwd(), ":~")

      local logo = opts.dashboard.preset.header

      local gradient = { "#c25400", "#a83f6e", "#3277f5", "#7b56e0", "#b83bc0", "#dd22ae" }
      local header = {}
      for i, line in ipairs(vim.split(logo, "\n", { plain = true })) do
        local hl = "SnacksDashboardHeaderGrad" .. i
        vim.api.nvim_set_hl(0, hl, { fg = gradient[i] or gradient[#gradient] })
        header[i] = { (i == 1 and "" or "\n") .. line, hl = hl }
      end
      table.insert(header, { "\n" })
      local cwd_line = "    " .. cwd
      table.insert(header, { "\n" .. cwd_line })

      opts.dashboard.preset.header = header
    end,
  },
}
