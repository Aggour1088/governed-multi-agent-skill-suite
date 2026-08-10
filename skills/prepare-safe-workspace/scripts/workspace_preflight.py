#!/usr/bin/env python3
"""Print a non-mutating repository preflight inventory."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run(root: Path, *args: str) -> tuple[int, str]:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    return result.returncode, (result.stdout + result.stderr).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    args = parser.parse_args()
    root = args.project_root.resolve()
    if not root.is_dir():
        print(f"FAIL: project root does not exist: {root}")
        return 1
    code, top = run(root, "rev-parse", "--show-toplevel")
    if code:
        print(f"FAIL: not a Git repository: {top}")
        return 1
    revision_code, revision = run(root, "rev-parse", "--short", "HEAD")
    if revision_code:
        revision = "unborn"
    _, status = run(root, "status", "--short")
    _, worktrees = run(root, "worktree", "list", "--porcelain")
    print(f"REPOSITORY: {top}")
    print(f"REVISION: {revision or 'unborn'}")
    print("STATUS:")
    print(status or "clean")
    print("WORKTREES:")
    print(worktrees or "default only")
    print("NOTE: this inventory is non-mutating and does not replace project baseline checks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
