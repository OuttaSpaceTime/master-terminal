local viewed_state_path = vim.fs.joinpath(vim.fn.stdpath("state"), "diffview-viewed.json")
local viewed_ns = vim.api.nvim_create_namespace("diffview_viewed")
local viewed_store

local function load_viewed_store()
  if viewed_store then
    return viewed_store
  end
  viewed_store = {}
  if vim.fn.filereadable(viewed_state_path) == 1 then
    local ok, decoded = pcall(vim.json.decode, table.concat(vim.fn.readfile(viewed_state_path), "\n"))
    if ok and type(decoded) == "table" then
      viewed_store = decoded
    end
  end
  return viewed_store
end

local function viewed_for(view)
  local store = load_viewed_store()
  local root = view.adapter.ctx.toplevel
  store[root] = store[root] or {}
  return store[root]
end

local function save_viewed_store()
  vim.fn.writefile({ vim.json.encode(load_viewed_store()) }, viewed_state_path)
end

local function render_viewed(view)
  if not view.panel.bufid or not vim.api.nvim_buf_is_valid(view.panel.bufid) then
    return
  end
  local viewed = viewed_for(view)
  vim.api.nvim_buf_clear_namespace(view.panel.bufid, viewed_ns, 0, -1)
  view.panel.components.comp:deep_some(function(comp)
    if comp.name == "file" and viewed[comp.context.path] then
      vim.api.nvim_buf_set_extmark(view.panel.bufid, viewed_ns, comp.lstart, 2, {
        virt_text = { { "✓", "DiffviewFilePanelInserted" } },
        virt_text_pos = "overlay",
      })
    end
    return false
  end)
end

local function viewed_target(view)
  if vim.bo.filetype == "DiffviewFiles" then
    local item = view.panel:get_item_at_cursor()
    return item and item.path
  end
  return view.cur_entry and view.cur_entry.path
end

local function toggle_viewed()
  local view = require("diffview.lib").get_current_view()
  if not view then
    return
  end
  local path = viewed_target(view)
  if not path then
    return
  end
  local viewed = viewed_for(view)
  if viewed[path] then
    viewed[path] = nil
  else
    viewed[path] = true
  end
  save_viewed_store()
  render_viewed(view)
end

local function clear_viewed()
  local view = require("diffview.lib").get_current_view()
  if not view then
    return
  end
  load_viewed_store()[view.adapter.ctx.toplevel] = nil
  save_viewed_store()
  render_viewed(view)
end

vim.api.nvim_create_autocmd({ "BufEnter", "CursorMoved" }, {
  group = vim.api.nvim_create_augroup("diffview-viewed", { clear = true }),
  callback = function()
    if vim.bo.filetype ~= "DiffviewFiles" then
      return
    end
    local view = require("diffview.lib").get_current_view()
    if view then
      render_viewed(view)
    end
  end,
})

local function goto_open_diffview()
  local views = require("diffview.lib").views
  local tabs = {}
  for _, view in ipairs(views) do
    if view.tabpage and vim.api.nvim_tabpage_is_valid(view.tabpage) then
      tabs[#tabs + 1] = view.tabpage
    end
  end
  if #tabs == 0 then
    vim.notify("No open Diffview", vim.log.levels.INFO)
    return
  end
  local cur = vim.api.nvim_get_current_tabpage()
  local idx
  for i, tab in ipairs(tabs) do
    if tab == cur then
      idx = i
      break
    end
  end
  -- On a diffview: go to the next one. Otherwise: go to the first.
  local target = idx and tabs[(idx % #tabs) + 1] or tabs[1]
  vim.api.nvim_set_current_tabpage(target)
end

return {
  {
    "sindrets/diffview.nvim",
    cmd = { "DiffviewOpen", "DiffviewClose", "DiffviewToggleFiles", "DiffviewFocusFiles", "DiffviewRefresh" },
    keys = {
      { "<leader>gv", "<cmd>DiffviewOpen<cr>", desc = "Git Diffview" },
      -- Close via <cmd> (not `:`) so noice's cmdline popup buffer never flashes
      -- into the tab — typing `:DiffviewClose` triggers E445 (the modified noice
      -- buffer blocks tabclose). See sindrets/diffview.nvim#302.
      { "<leader>gc", "<cmd>DiffviewClose<cr>", desc = "Close Diffview" },
      { "<leader>Dc", "<cmd>DiffviewClose<cr>", desc = "Close Diffview" },
      { "<leader>Dr", "<cmd>DiffviewRefresh<cr>", desc = "Refresh Diffview" },
      { "<leader>Dv", toggle_viewed, desc = "Toggle Viewed Mark" },
      { "<leader>DV", clear_viewed, desc = "Clear Viewed Marks" },
      {
        "<leader>Dl",
        "<cmd>DiffviewOpen main...HEAD --imply-local<cr>",
        desc = "Diffview Since Main (local files)",
      },
      {
        "<leader>Dp",
        function()
          Snacks.picker.git_log({
            cmd_args = { "-n", "30" },
            confirm = function(picker, item)
              picker:close()
              if item and item.commit then
                vim.cmd("DiffviewOpen " .. item.commit .. "...HEAD --imply-local")
              end
            end,
          })
        end,
        desc = "Diffview Since Commit (local files)",
      },
      {
        "<leader>gj",
        goto_open_diffview,
        desc = "Go to open Diffview",
      },
      {
        "gj",
        goto_open_diffview,
        desc = "Go to open Diffview",
      },
      {
        "<leader>gM",
        function()
          local base = "origin/main"
          if vim.fn.systemlist({ "git", "rev-parse", "--verify", "origin/main" })[1] == nil
            or vim.v.shell_error ~= 0
          then
            base = "origin/master"
          end
          vim.cmd("DiffviewOpen " .. base .. "...HEAD")
        end,
        desc = "Git Diffview Since Main",
      },
      { "<leader>gF", "<cmd>DiffviewFocusFiles<cr>", desc = "Git Diffview Files" },
      { "<leader>gt", "<cmd>DiffviewToggleFiles<cr>", desc = "Git Diffview Toggle Files" },
      { "<leader>gV", "<cmd>DiffviewFileHistory %<cr>", desc = "Git File History" },
    },
    opts = {
      enhanced_diff_hl = true,
      use_icons = true,
      view = {
        merge_tool = {
          layout = "diff3_mixed",
        },
      },
    },
  },
  {
    "folke/which-key.nvim",
    opts = {
      spec = {
        { "<leader>D", group = "diffview" },
      },
    },
  },
}
