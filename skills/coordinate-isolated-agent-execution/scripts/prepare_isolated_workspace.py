#!/usr/bin/env python3
"""Preview or create one non-destructive Git worktree for an active v2 contract."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def fail(message: str) -> int:
    print(f"FAIL: {message}")
    return 1


def git_root(project_root: Path) -> Path:
    result = subprocess.run(
        ["git", "-C", str(project_root), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise ValueError("project_root must be an existing Git repository")
    root = Path(result.stdout.strip()).resolve(strict=True)
    if root != project_root.resolve(strict=True):
        raise ValueError("project_root must be the repository root, not a nested directory")
    return root


def load_contract(path: Path) -> dict:
    rules_dir = Path(__file__).resolve().parents[2] / "using-governed-suite" / "scripts"
    if not rules_dir.is_dir():
        raise ValueError("using-governed-suite must be installed with this coordinator")
    if str(rules_dir) not in sys.path:
        sys.path.insert(0, str(rules_dir))
    from contract_rules import load_contract as load  # noqa: PLC0415

    return load(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--apply", action="store_true", help="create the worktree after validation")
    args = parser.parse_args()
    try:
        contract = load_contract(args.contract)
        root = git_root(args.project_root)
        workspace = args.workspace.absolute()
        if workspace.exists() or workspace.is_symlink():
            raise ValueError("workspace target already exists; never merge or overwrite a worktree")
        parent = workspace.parent.resolve(strict=True)
        if root == parent or root in parent.parents:
            raise ValueError("workspace must be outside the repository root")
        if contract.get("status") != "active" or not contract.get("authority", {}).get("mutation_allowed"):
            raise ValueError("an active mutation-authorized contract is required")
        baseline = contract["project"]["baseline_revision"]
        baseline_check = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--verify", f"{baseline}^{{commit}}"],
            capture_output=True,
            text=True,
            check=False,
        )
        if baseline_check.returncode:
            raise ValueError("contract baseline_revision is not available in this repository")
    except (OSError, ValueError) as exc:
        return fail(str(exc))

    command = ["git", "-C", str(root), "worktree", "add", "--detach", str(workspace), baseline]
    if not args.apply:
        print("WOULD_CREATE: " + " ".join(command))
        return 0
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode:
        return fail((result.stdout + result.stderr).strip() or "git worktree creation failed")
    print(f"CREATED: {workspace}")
    print("NEXT: create and validate the durable ledger before implementation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
