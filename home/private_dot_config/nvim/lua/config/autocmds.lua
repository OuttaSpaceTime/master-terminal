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
  local root = vim.fs.normalize(LazyVim.root.get())
  local file = vim.api.nvim_buf_get_name(0)
  local path
  if file == "" then
    path = "[No Name]"
  else
    local abs = vim.fs.normalize(file)
    if abs:sub(1, #root + 1) == root .. "/" then
      path = abs:sub(#root + 2) -- path relative to the project root
    else
      path = vim.fn.fnamemodify(file, ":t") -- outside root: fall back to filename
    end
  end
  vim.opt.title = true
  vim.opt.titlestring = ("nvim %s"):format(path)
end

vim.api.nvim_create_autocmd({ "VimEnter", "DirChanged", "BufEnter" }, {
  group = title_group,
  callback = update_project_title,
})

-- Aggressively check for external file changes (e.g. Claude Code edits)
-- so `autoread` actually kicks in without manual :checktime.
local checktime_group = vim.api.nvim_create_augroup("auto_checktime", { clear = true })

vim.api.nvim_create_autocmd({ "FocusGained", "BufEnter", "CursorHold", "CursorHoldI", "TermLeave" }, {
  group = checktime_group,
  pattern = "*",
  callback = function()
    if vim.fn.getcmdwintype() == "" and vim.bo.buftype ~= "nofile" then
      pcall(vim.cmd, "checktime")
    end
  end,
})

vim.api.nvim_create_autocmd("FileChangedShellPost", {
  group = checktime_group,
  pattern = "*",
  callback = function()
    vim.notify("File changed on disk — buffer reloaded.", vim.log.levels.INFO)
  end,
})

local agent_socket_group = vim.api.nvim_create_augroup("agent_nvim_socket", { clear = true })

local function agent_socket_registry_path()
  local root = LazyVim.root.get()
  local folder = vim.fs.basename(root)
  local hash = vim.fn.sha256(root):sub(1, 12)
  local dir = (vim.env.XDG_RUNTIME_DIR or vim.fn.stdpath("run") or "/tmp") .. "/nvim-agent"

  vim.fn.mkdir(dir, "p")
  return ("%s/%s-%s.sockpath"):format(dir, folder, hash)
end

local function write_agent_socket_registry()
  local server = vim.v.servername
  if server == nil or server == "" then
    return
  end

  local path = agent_socket_registry_path()
  vim.fn.writefile({ server }, path)
  vim.g.agent_nvim_socket_registry = path
end

vim.api.nvim_create_autocmd({ "VimEnter", "DirChanged" }, {
  group = agent_socket_group,
  callback = write_agent_socket_registry,
})

vim.api.nvim_create_user_command("AgentNvimSocket", function()
  write_agent_socket_registry()
  local path = vim.g.agent_nvim_socket_registry
  if path == nil or path == "" then
    vim.notify("No Nvim server socket registered", vim.log.levels.WARN)
    return
  end

  vim.fn.setreg("+", path)
  vim.notify("Copied Nvim socket registry path: " .. path)
end, {})

local kitty_bg_group = vim.api.nvim_create_augroup("kitty_bg_sync", { clear = true })

vim.api.nvim_create_autocmd({ "UIEnter", "ColorScheme" }, {
  group = kitty_bg_group,
  callback = function()
    local normal = vim.api.nvim_get_hl(0, { name = "Normal" })
    if normal.bg then
      io.write(string.format("\027]11;#%06x\027\\", normal.bg))
    end
  end,
})

vim.api.nvim_create_autocmd("UILeave", {
  group = kitty_bg_group,
  callback = function()
    io.write("\027]111\027\\")
  end,
})

vim.api.nvim_create_autocmd("LspAttach", {
  callback = function(ev)
    if vim.api.nvim_buf_get_name(ev.buf):match("/gems/[^/]+/") then
      vim.diagnostic.enable(false, { bufnr = ev.buf })
    end
  end,
})
