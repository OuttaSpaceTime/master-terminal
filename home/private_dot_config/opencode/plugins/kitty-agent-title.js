import { spawn } from "node:child_process";
import { homedir } from "node:os";

const EVENTS = {
  "permission.asked": "PermissionRequest",
  "question.asked": "PermissionRequest",
  "session.idle": "Stop",
  "session.compacted": "PreCompact",
};

export const KittyAgentTitle = async ({ directory }) => {
  const title = (hook_event_name) => {
    const child = spawn(`${homedir()}/.local/bin/kitty-agent-title`, ["opencode"], {
      stdio: ["pipe", "ignore", "ignore"],
    });
    child.on("error", () => {});
    child.stdin.on("error", () => {});
    child.stdin.end(JSON.stringify({ hook_event_name, cwd: directory }));
  };

  title("SessionStart");

  return {
    "chat.message": async () => title("UserPromptSubmit"),
    "tool.execute.before": async () => title("PreToolUse"),
    "tool.execute.after": async () => title("PostToolUse"),
    event: async ({ event }) => {
      if (EVENTS[event.type]) title(EVENTS[event.type]);
    },
  };
};
