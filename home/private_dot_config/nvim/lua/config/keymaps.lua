-- Keymaps are automatically loaded on the VeryLazy event
-- Default keymaps that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/keymaps.lua
-- Add any additional keymaps here

local function copy_path_from_root(with_line)
  local file = vim.api.nvim_buf_get_name(0)
  if file == "" then
    vim.notify("No file path for current buffer", vim.log.levels.WARN)
    return
  end

  local root = LazyVim.root.get()
  local rel = vim.fn.fnamemodify(file, ":." .. root)
  if rel == file then
    rel = vim.fs.relpath(root, file) or vim.fn.fnamemodify(file, ":t")
  end
  rel = rel:gsub("^/", "")
  local value = with_line and (rel .. ":" .. vim.api.nvim_win_get_cursor(0)[1]) or rel
  vim.fn.setreg("+", value)
  vim.notify("Copied: " .. value)
end

vim.keymap.set("n", "<leader>fy", function()
  copy_path_from_root(false)
end, { desc = "Copy File Path (Root)" })

vim.keymap.set("n", "<leader>fY", function()
  copy_path_from_root(true)
end, { desc = "Copy File Path With Line (Root)" })

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

-- Trackball tab-switch gesture (BTN_EXTRA + ball left/right)
vim.keymap.set({ "n", "i", "t" }, "<C-Tab>", "<Cmd>bnext<CR>", { desc = "Next Buffer" })
vim.keymap.set({ "n", "i", "t" }, "<C-S-Tab>", "<Cmd>bprevious<CR>", { desc = "Prev Buffer" })
