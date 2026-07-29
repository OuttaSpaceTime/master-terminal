-- Keymaps are automatically loaded on the VeryLazy event
-- Default keymaps that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/keymaps.lua
-- Add any additional keymaps here

local function copy_path(root, with_line)
  local file = vim.api.nvim_buf_get_name(0)
  if file == "" then
    vim.notify("No file path for current buffer", vim.log.levels.WARN)
    return
  end
  if not root then
    vim.notify("Not in a git repository", vim.log.levels.WARN)
    return
  end

  local rel = vim.fn.fnamemodify(file, ":." .. root)
  if rel == file then
    rel = vim.fs.relpath(root, file) or vim.fn.fnamemodify(file, ":t")
  end
  rel = rel:gsub("^/", "")
  local value = with_line and (rel .. ":" .. vim.api.nvim_win_get_cursor(0)[1]) or rel
  vim.fn.setreg("+", value)
  vim.notify("Copied: " .. value)
end

local function git_root()
  local dir = vim.fs.dirname(vim.api.nvim_buf_get_name(0))
  local out = vim.fn.systemlist({ "git", "-C", dir, "rev-parse", "--show-toplevel" })
  return vim.v.shell_error == 0 and out[1] or nil
end

vim.keymap.set("n", "<leader>fyp", function() copy_path(LazyVim.root.get(), false) end, { desc = "Copy Path (Root)" })
vim.keymap.set("n", "<leader>fyl", function() copy_path(LazyVim.root.get(), true) end, { desc = "Copy Path + Line (Root)" })
vim.keymap.set("n", "<leader>fyP", function() copy_path(git_root(), false) end, { desc = "Copy Path (Git Root)" })
vim.keymap.set("n", "<leader>fyL", function() copy_path(git_root(), true) end, { desc = "Copy Path + Line (Git Root)" })

local smart_splits = require("smart-splits")

vim.keymap.set("n", "<C-h>", smart_splits.move_cursor_left, { desc = "Move Left" })
vim.keymap.set("n", "<C-j>", smart_splits.move_cursor_down, { desc = "Move Down" })
vim.keymap.set("n", "<C-k>", smart_splits.move_cursor_up, { desc = "Move Up" })
vim.keymap.set("n", "<C-l>", smart_splits.move_cursor_right, { desc = "Move Right" })

vim.keymap.set("n", "<A-h>", smart_splits.resize_left, { desc = "Resize Left" })
vim.keymap.set("n", "<A-j>", smart_splits.resize_down, { desc = "Resize Down" })
vim.keymap.set("n", "<A-k>", smart_splits.resize_up, { desc = "Resize Up" })
vim.keymap.set("n", "<A-l>", smart_splits.resize_right, { desc = "Resize Right" })

vim.keymap.set("n", "<leader>gR", function()
  Snacks.picker.resume("git_diff")
end, { desc = "Resume Git Diff" })
vim.keymap.set("n", "<leader>gg", function()
  Snacks.lazygit({ cwd = LazyVim.root.git() })
end, { desc = "Lazygit (Root Dir)" })

vim.keymap.set("n", "<leader>gG", function()
  Snacks.lazygit()
end, { desc = "Lazygit (cwd)" })

-- Trackball tab-switch gesture (BTN_EXTRA + ball left/right)
vim.keymap.set({ "n", "i", "t" }, "<C-Tab>", "<Cmd>bnext<CR>", { desc = "Next Buffer" })
vim.keymap.set({ "n", "i", "t" }, "<C-S-Tab>", "<Cmd>bprevious<CR>", { desc = "Prev Buffer" })

-- Switch tabpage (same as gt/gT): Ctrl+Alt+Shift+H/L
vim.keymap.set("n", "<C-A-S-h>", "<Cmd>tabprevious<CR>", { desc = "Prev Tab" })
vim.keymap.set("n", "<C-A-S-l>", "<Cmd>tabnext<CR>", { desc = "Next Tab" })

vim.keymap.set("n", "<leader>tn", "<Cmd>tabnew<CR>", { desc = "New Tab" })
vim.keymap.set("n", "<leader>tc", "<Cmd>tabclose<CR>", { desc = "Close Tab" })
vim.keymap.set("n", "<leader>tl", "<Cmd>tabnext<CR>", { desc = "Next Tab" })
vim.keymap.set("n", "<leader>th", "<Cmd>tabprevious<CR>", { desc = "Prev Tab" })
