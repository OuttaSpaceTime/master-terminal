-- Autocmds are automatically loaded on the VeryLazy event
-- Default autocmds that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/autocmds.lua
--
-- Add any additional autocmds here
-- with `vim.api.nvim_create_autocmd`
--
-- Or remove existing autocmds by their group name (which is prefixed with `lazyvim_` for the defaults)
-- e.g. vim.api.nvim_del_augroup_by_name("lazyvim_wrap_spell")

local title_group = vim.api.nvim_create_augroup("kitty_project_title", { clear = true })

local function update_project_title()
  local root = LazyVim.root.get()
  local folder = vim.fs.basename(root)
  local file = vim.api.nvim_buf_get_name(0)
  local filename = file ~= "" and vim.fn.fnamemodify(file, ":t") or "[No Name]"
  vim.opt.title = true
  vim.opt.titlestring = ("nvim %s %s"):format(folder, filename)
end

vim.api.nvim_create_autocmd({ "VimEnter", "DirChanged", "BufEnter" }, {
  group = title_group,
  callback = update_project_title,
})
