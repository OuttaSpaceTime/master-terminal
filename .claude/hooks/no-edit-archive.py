#!/usr/bin/env python3
"""PreToolUse guard: refuse edits to archived skills.

Files under home/dot_agents/skills-archive/ are preserved-but-inactive: nothing
there deploys, and the content must stay a faithful snapshot of when it was
archived. Restore the skill first (agent-skills-archive --restore <name>) and
edit the active source under home/dot_agents/skills/ instead.

Exit 2 blocks the Edit/Write/MultiEdit call. Fails open: any internal error
allows the tool call so a bug here never wedges a session.
"""
import json
import sys


def main():
    data = json.load(sys.stdin)
    fp = (data.get("tool_input") or {}).get("file_path", "") or ""
    if "dot_agents/skills-archive/" in fp:
        sys.stderr.write(
            f"Refusing to edit an archived skill ({fp}). "
            "home/dot_agents/skills-archive/ is preserved-but-inactive — nothing "
            "there deploys, so editing it has no live effect. Restore it first: "
            "agent-skills-archive --restore <name>, then edit the active source "
            "under home/dot_agents/skills/.\n"
        )
        sys.exit(2)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        sys.exit(0)  # fail open
