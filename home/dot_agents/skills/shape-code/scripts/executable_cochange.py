#!/usr/bin/env python3
"""Change coupling and hot spots for the files of a diff, from git history.

For each file the diff touches, prints how often it changed (churn) and which other
files changed in the same commits (co-changes), with the coupling degree:
shared commits / commits of the diff file. Files that keep changing together across
layers hint at a rule spread over several places (shotgun surgery); files that change
often and are large are hot spots where placement matters most.

Usage: cochange.py [BASE] [--commits N] [--min-shared K] [--top T]
  BASE         diff base (default: HEAD, i.e. uncommitted work; a branch works too)
  --commits    how many recent non-merge commits to read (default 1000)
  --min-shared ignore pairs with fewer shared commits (default 3: one or two
               shared commits happen by coincidence, three start a pattern)
  --top        co-changes to show per file (default 6)

Commits touching more than 30 files are skipped: mass renames and formatting runs
couple everything with everything. Standard library only.
"""
import argparse
import subprocess
import sys
from collections import Counter

MAX_FILES_PER_COMMIT = 30


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def diff_files(base):
    tracked = git("diff", "--name-only", base).split()
    untracked = git("ls-files", "--others", "--exclude-standard").split()
    return sorted(set(tracked) | set(untracked))


def commits(n):
    log = git("log", "--no-merges", f"-n{n}", "--format=%x00", "--name-only")
    for chunk in log.split("\x00"):
        files = {line for line in chunk.splitlines() if line.strip()}
        if 0 < len(files) <= MAX_FILES_PER_COMMIT:
            yield files


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("base", nargs="?", default="HEAD")
    parser.add_argument("--commits", type=int, default=1000)
    parser.add_argument("--min-shared", type=int, default=3)
    parser.add_argument("--top", type=int, default=6)
    args = parser.parse_args()

    try:
        targets = diff_files(args.base)
        history = list(commits(args.commits))
    except subprocess.CalledProcessError as error:
        sys.exit(error.stderr.strip())
    if not targets:
        sys.exit(f"No changes against {args.base}.")

    print(f"Read {len(history)} commits (<= {MAX_FILES_PER_COMMIT} files each).\n")
    for target in targets:
        touching = [files for files in history if target in files]
        print(f"{target}: {len(touching)} commits")
        partners = Counter(other for files in touching for other in files if other != target)
        shown = [(other, shared) for other, shared in partners.most_common()
                 if shared >= args.min_shared][: args.top]
        for other, shared in shown:
            print(f"  {shared / len(touching):4.0%}  {shared:3d} shared  {other}")
        if touching and not shown:
            print("  no co-changes above the threshold")
        print()


if __name__ == "__main__":
    main()
