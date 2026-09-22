#!/usr/bin/env python3
"""Map local-review.nvim comments onto the hunks of the current branch's diff.

Answers one question: which parts of this change has the reviewer not looked at yet?

The diff is taken against the *working tree*, not HEAD, because comment anchors are
line numbers in the files as they currently sit on disk. Diffing `base...HEAD` instead
would shift every line number by whatever is uncommitted and silently mis-attribute
comments to the wrong hunks.
"""

import argparse
import fnmatch
import json
import re
import subprocess
import sys

HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)")

# Files a human reviewer reads differently. Nothing is hidden — these are still listed
# and still counted, just kept out of the headline so a few hundred lines of regenerated
# fixtures cannot drown out the handful of hunks that actually encode a decision.
DEFAULT_GENERATED = [
    "db/schema.rb",
    "db/structure.sql",
    "test/fixtures/*",
    "spec/fixtures/*",
    "*.lock",
    "package-lock.json",
    "yarn.lock",
    "Gemfile.lock",
]
DEFAULT_TEST = ["test/*", "spec/*", "*_test.rb", "*_spec.rb", "*.test.ts", "*.spec.ts"]


def bucket_for(path, generated, tests):
    if any(fnmatch.fnmatch(path, pat) for pat in generated):
        return "generated"
    if any(fnmatch.fnmatch(path, pat) for pat in tests):
        return "test"
    return "source"


def git(*args, cwd=None):
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True
    ).stdout


def default_base(cwd=None):
    """Merge base with whichever integration branch this repo actually uses."""
    for candidate in ("main", "master", "origin/main", "origin/master"):
        try:
            return git("merge-base", candidate, "HEAD", cwd=cwd).strip()
        except subprocess.CalledProcessError:
            continue
    raise SystemExit("could not find a merge base against main/master; pass --base")


def parse_hunks(diff_text):
    """Yield one record per hunk, carrying its new-side line span and its body."""
    hunks = []
    path = None
    current = None

    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            path = line.split(" b/", 1)[-1]
            current = None
            continue
        m = HUNK_RE.match(line)
        if m:
            new_start = int(m.group(3))
            new_count = int(m.group(4)) if m.group(4) is not None else 1
            current = {
                "path": path,
                "new_start": new_start,
                "new_end": new_start + max(new_count, 1) - 1,
                "pure_deletion": new_count == 0,
                "header": m.group(5).strip(),
                "body": [],
                "changed_lines": [],
            }
            hunks.append(current)
            continue
        if current is None:
            continue
        current["body"].append(line)
        if line.startswith(("+", "-")) and not line.startswith(("+++", "---")):
            current["changed_lines"].append(line)

    return hunks


def covers(comment, hunk, slop):
    if comment["path"] != hunk["path"]:
        return False
    lo = hunk["new_start"] - (slop if hunk["pure_deletion"] else 0)
    hi = hunk["new_end"] + (slop if hunk["pure_deletion"] else 0)
    return comment["line"] <= hi and comment["line_end"] >= lo


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", help="base ref (default: merge-base with main/master)")
    ap.add_argument("--comments", help="comments JSON file (default: stdin)")
    ap.add_argument("--json", dest="json_out", help="also write the full record here")
    ap.add_argument(
        "--slop",
        type=int,
        default=3,
        help="lines of tolerance when matching a comment to a pure-deletion hunk",
    )
    ap.add_argument("--repo", default=None, help="repository path (default: cwd)")
    ap.add_argument(
        "--generated",
        action="append",
        default=None,
        help="glob for generated/derived files, kept out of the headline (repeatable)",
    )
    ap.add_argument(
        "--max-gaps",
        type=int,
        default=6,
        help="uncommented hunks listed per file before truncating (0 = no limit)",
    )
    args = ap.parse_args()

    generated = args.generated if args.generated is not None else DEFAULT_GENERATED

    base = args.base or default_base(args.repo)

    raw = (
        open(args.comments).read()
        if args.comments
        else sys.stdin.read()
    )
    comments = json.loads(raw) if raw.strip() else []

    diff = git("diff", base, "--", ".", cwd=args.repo)
    hunks = parse_hunks(diff)

    for hunk in hunks:
        hunk["comments"] = [c["body"] for c in comments if covers(c, hunk, args.slop)]
        hunk["bucket"] = bucket_for(hunk["path"], generated, DEFAULT_TEST)

    by_file = {}
    for hunk in hunks:
        entry = by_file.setdefault(
            hunk["path"], {"total": 0, "covered": 0, "gaps": [], "bucket": hunk["bucket"]}
        )
        entry["total"] += 1
        if hunk["comments"]:
            entry["covered"] += 1
        else:
            entry["gaps"].append(hunk)

    total = len(hunks)
    covered = sum(1 for h in hunks if h["comments"])
    orphans = [c for c in comments if not any(covers(c, h, args.slop) for h in hunks)]

    print(f"base {base[:12]}  ..  working tree")
    print(f"comments {len(comments)}   outside any hunk {len(orphans)}")
    print()
    for bucket in ("source", "test", "generated"):
        picked = [h for h in hunks if h["bucket"] == bucket]
        if not picked:
            continue
        hit = sum(1 for h in picked if h["comments"])
        print(f"  {bucket:<10} {hit:>3}/{len(picked):<4} commented")
    print(f"  {'total':<10} {covered:>3}/{total:<4} commented")
    print()

    for bucket in ("source", "test", "generated"):
        paths = [p for p in sorted(by_file) if by_file[p]["bucket"] == bucket]
        if not paths:
            continue
        print(f"--- {bucket} ---")
        for path in paths:
            entry = by_file[path]
            flag = " " if entry["covered"] == entry["total"] else "!"
            print(f"{flag} {path}  ({entry['covered']}/{entry['total']})")
            gaps = entry["gaps"]
            shown = gaps if args.max_gaps == 0 else gaps[: args.max_gaps]
            for gap in shown:
                span = (
                    f"L{gap['new_start']}"
                    if gap["new_start"] == gap["new_end"]
                    else f"L{gap['new_start']}-{gap['new_end']}"
                )
                changed = len(gap["changed_lines"])
                ctx = f"  {gap['header'][:60]}" if gap["header"] else ""
                print(f"      uncommented {span}  ({changed} changed lines){ctx}")
            if len(gaps) > len(shown):
                print(f"      ... {len(gaps) - len(shown)} more uncommented hunks")
        print()

    if orphans:
        print()
        print("comments that match no hunk (unchanged code, or a stale anchor):")
        for c in orphans:
            print(f"  {c['path']}:{c['line']}  {c['body'][:70]}")

    if args.json_out:
        with open(args.json_out, "w") as fh:
            json.dump(
                {
                    "base": base,
                    "totals": {
                        "hunks": total,
                        "covered": covered,
                        "uncovered": total - covered,
                        "comments": len(comments),
                    },
                    "hunks": [
                        {
                            "path": h["path"],
                            "bucket": h["bucket"],
                            "new_start": h["new_start"],
                            "new_end": h["new_end"],
                            "header": h["header"],
                            "changed_lines": len(h["changed_lines"]),
                            "comments": h["comments"],
                            "diff": "\n".join(h["body"]),
                        }
                        for h in hunks
                    ],
                    "orphan_comments": orphans,
                },
                fh,
                indent=2,
            )


if __name__ == "__main__":
    main()
