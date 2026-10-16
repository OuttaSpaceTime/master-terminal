-- Options are automatically loaded before lazy.nvim startup
-- Default options that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/options.lua
-- Add any additional options here
vim.g.python3_host_prog = vim.fn.expand('~/.venvs/pynvim/bin/python')
vim.g.ruby_host_prog = vim.fn.expand('~/.rbenv/versions/4.0.1/bin/neovim-ruby-host')
vim.g.lazyvim_prettier_needs_config = true

vim.opt.relativenumber = false

-- Root detection: when inside an installed gem (.../gems/<name>-<version>/...),
-- scope the root to that single gem dir. Otherwise rbenv's own .git would make
-- the `.git` detector resolve root to ~/.rbenv, breaking search in gem code.
vim.g.root_spec = {
  -- Inside a SolveIt scratch folder (.solve/tasks/<X>, possibly its own git repo),
  -- use the main repo that holds .solve.
  function(buf)
    local name = vim.api.nvim_buf_get_name(buf or 0)
    local main = name:match('^(.*)/%.solve/') or vim.fn.getcwd():match('^(.*)/%.solve/')
    if main then
      return { main }
    end
  end,
  function(buf)
    local name = vim.api.nvim_buf_get_name(buf or 0)
    local gem_root = name:match('^(.*/gems/[^/]+)/?')
      or vim.fn.getcwd():match('^(.*/gems/[^/]+)/?')
    if gem_root and vim.fn.isdirectory(gem_root) == 1 then
      return { gem_root }
    end
  end,
  'lsp',
  { '.git', 'lua' },
  'cwd',
}
