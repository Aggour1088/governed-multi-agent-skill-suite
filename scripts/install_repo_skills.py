#!/usr/bin/env python3
"""Install an exact, validated suite copy into an empty repository skill scope.

This tool is deliberately limited to a repository root's `.agents/skills`
directory. It never merges, replaces, or updates an existing skill collection.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path


def fail(message: str) -> int:
    print(f"FAIL: {message}")
    return 1


def resolve_directory(raw_path: str, label: str) -> Path:
    try:
        path = Path(raw_path).resolve(strict=True)
    except OSError as exc:
        raise ValueError(f"{label} cannot be resolved: {exc}") from exc
    if not path.is_dir():
        raise ValueError(f"{label} must be a directory")
    return path


def repository_root(project_root: Path) -> Path:
    result = subprocess.run(
        ["git", "-C", str(project_root), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise ValueError("PROJECT_ROOT must be an existing Git repository root")
    try:
        git_root = Path(result.stdout.strip()).resolve(strict=True)
    except OSError as exc:
        raise ValueError(f"cannot resolve Git repository root: {exc}") from exc
    if git_root != project_root:
        raise ValueError("PROJECT_ROOT must be the Git repository root, not a nested directory")
    return git_root


def validate_source_suite(suite_root: Path) -> list[str]:
    """Run the suite's published deterministic checks before any project write."""
    commands = (
        ("release checksums", [sys.executable, str(suite_root / "scripts" / "release_checksums.py")]),
        ("suite validation", [sys.executable, str(suite_root / "scripts" / "validate_suite.py")]),
        (
            "evaluation fixture validation",
            [sys.executable, str(suite_root / "scripts" / "validate_evaluation_suite.py")],
        ),
    )
    errors: list[str] = []
    for label, command in commands:
        result = subprocess.run(command, cwd=suite_root, text=True, capture_output=True, check=False)
        if result.returncode:
            output = (result.stdout + result.stderr).strip().replace("\n", " | ")
            errors.append(f"{label} failed: {output or 'no diagnostic output'}")
    return errors


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def skill_tree_manifest(root: Path) -> dict[str, tuple[str, str | None]]:
    """Return a safe, content-addressed manifest for one skills directory."""
    if root.is_symlink() or not root.is_dir():
        raise ValueError(f"skill tree is not a regular directory: {root}")

    entries: dict[str, tuple[str, str | None]] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        try:
            mode = path.lstat().st_mode
        except OSError as exc:
            raise ValueError(f"cannot inspect skill-tree path {relative}: {exc}") from exc
        if stat.S_ISLNK(mode):
            raise ValueError(f"skill tree contains a symlink: {relative}")
        if stat.S_ISDIR(mode):
            entries[relative] = ("directory", None)
            continue
        if not stat.S_ISREG(mode):
            raise ValueError(f"skill tree contains a non-regular file: {relative}")
        entries[relative] = ("file", sha256_file(path))
    return entries


def compare_manifest_to_tree(
    source_manifest: dict[str, tuple[str, str | None]], destination: Path
) -> list[str]:
    try:
        destination_manifest = skill_tree_manifest(destination)
    except ValueError as exc:
        return [str(exc)]
    if source_manifest == destination_manifest:
        return []

    errors: list[str] = ["installed skill tree does not exactly match the verified source skill tree"]
    missing = sorted(set(source_manifest) - set(destination_manifest))
    unexpected = sorted(set(destination_manifest) - set(source_manifest))
    changed = sorted(
        relative
        for relative in set(source_manifest) & set(destination_manifest)
        if source_manifest[relative] != destination_manifest[relative]
    )
    if missing:
        errors.append("missing: " + ", ".join(missing[:5]))
    if unexpected:
        errors.append("unexpected: " + ", ".join(unexpected[:5]))
    if changed:
        errors.append("changed: " + ", ".join(changed[:5]))
    return errors


def safe_destination(project_root: Path) -> tuple[Path, Path, bool]:
    """Validate the destination without creating or deleting any project path."""
    agents_root = project_root / ".agents"
    if agents_root.exists() or agents_root.is_symlink():
        if agents_root.is_symlink() or not agents_root.is_dir():
            raise ValueError(f"destination parent is not a regular directory: {agents_root}")
        agents_exists = True
    else:
        agents_exists = False

    destination = agents_root / "skills"
    if destination.exists() or destination.is_symlink():
        if destination.is_symlink() or not destination.is_dir():
            raise ValueError(f"destination collision: {destination}")
        try:
            first_entry = next(destination.iterdir(), None)
        except OSError as exc:
            raise ValueError(f"cannot inspect destination: {destination}: {exc}") from exc
        if first_entry is not None:
            raise ValueError("destination is not empty: do not merge or overwrite existing skills")
    return agents_root, destination, agents_exists


def install(
    source_skills: Path,
    source_manifest: dict[str, tuple[str, str | None]],
    project_root: Path,
) -> list[str]:
    try:
        agents_root, destination, agents_exists = safe_destination(project_root)
    except ValueError as exc:
        return [str(exc)]
    staging: Path | None = None
    destination_was_empty = destination.exists() and destination.is_dir()
    try:
        if not agents_exists:
            agents_root.mkdir(mode=0o755)
        if destination_was_empty:
            destination.rmdir()
        staging = Path(tempfile.mkdtemp(prefix=".governed-suite-", dir=agents_root))
        for skill_directory in sorted(path for path in source_skills.iterdir() if path.is_dir()):
            shutil.copytree(skill_directory, staging / skill_directory.name, copy_function=shutil.copy2)
        errors = compare_manifest_to_tree(source_manifest, staging)
        if errors:
            return errors
        staging.replace(destination)
        staging = None
        return compare_manifest_to_tree(source_manifest, destination)
    except OSError as exc:
        return [f"cannot install skills safely: {exc}"]
    finally:
        if staging is not None and staging.exists():
            shutil.rmtree(staging)
        if not agents_exists and agents_root.exists():
            try:
                agents_root.rmdir()
            except OSError:
                pass


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite-dir", required=True, help="absolute or relative path to the verified suite checkout")
    parser.add_argument("--project-root", required=True, help="path to the target Git repository root")
    parser.add_argument(
        "--verify-installed",
        action="store_true",
        help="verify an existing installed copy without writing to the project",
    )
    args = parser.parse_args()

    try:
        suite_root = resolve_directory(args.suite_dir, "SUITE_DIR")
        project_root = repository_root(resolve_directory(args.project_root, "PROJECT_ROOT"))
    except ValueError as exc:
        return fail(str(exc))

    source_skills = suite_root / "skills"
    if source_skills.is_symlink() or not source_skills.is_dir():
        return fail("source suite has no regular skills directory")

    source_errors = validate_source_suite(suite_root)
    if source_errors:
        print("FAIL: source suite validation failed; no project files were written")
        for error in source_errors:
            print(f"- {error}")
        return 1

    try:
        source_manifest = skill_tree_manifest(source_skills)
    except ValueError as exc:
        return fail(f"cannot capture the verified source skill tree: {exc}")

    if args.verify_installed:
        destination = project_root / ".agents" / "skills"
        errors = compare_manifest_to_tree(source_manifest, destination)
        if errors:
            print("FAIL: installed copy verification failed")
            for error in errors:
                print(f"- {error}")
            return 1
        print(f"PASS: installed copy exactly matches the verified 20-skill source at {destination}")
        return 0

    errors = install(source_skills, source_manifest, project_root)
    if errors:
        print("FAIL: installation stopped")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"PASS: installed 20 exact skill folders at {project_root / '.agents' / 'skills'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
