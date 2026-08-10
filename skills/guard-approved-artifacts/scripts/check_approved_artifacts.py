#!/usr/bin/env python3
"""Check that downstream artifacts are cryptographically bound to an approved Foundation."""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import stat
import sys
from pathlib import Path, PurePosixPath


FINGERPRINT = re.compile(r"^sha256:[0-9a-f]{64}$")


def frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        raise ValueError("artifact is missing frontmatter")
    parts = text.split("---\n", 2)
    if len(parts) != 3:
        raise ValueError("artifact frontmatter is malformed")
    values: dict[str, str] = {}
    for line in parts[1].splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            raise ValueError(f"invalid frontmatter line: {line!r}")
        key, value = line.split(":", 1)
        key = key.strip()
        if not key or key in values:
            raise ValueError(f"invalid or duplicate frontmatter key: {key!r}")
        values[key] = value.strip().strip('"').strip("'")
    return values


def _identity(info: os.stat_result) -> tuple[int, int, int]:
    return info.st_dev, info.st_ino, stat.S_IFMT(info.st_mode)


def _safe_open_flags(*, directory: bool) -> int:
    """Return the POSIX-only flags needed for descriptor-bound traversal."""
    if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
        raise ValueError("safe artifact reads require POSIX O_NOFOLLOW, O_DIRECTORY, and dir_fd support")
    flags = os.O_RDONLY | os.O_NOFOLLOW
    if directory:
        flags |= os.O_DIRECTORY
    elif hasattr(os, "O_NONBLOCK"):
        flags |= os.O_NONBLOCK
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    return flags


def safe_regular_file(root: Path, value: Path | str, label: str) -> tuple[int, str]:
    """Open a contained regular file without reopening child paths by name."""
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("project_root is not a directory")
    candidate = Path(value)
    if candidate.is_absolute():
        try:
            relative_path = candidate.relative_to(root)
        except ValueError as exc:
            raise ValueError(f"{label} is outside project_root") from exc
    else:
        relative_path = candidate
    raw = relative_path.as_posix()
    if "\\" in raw:
        raise ValueError(f"{label} path must use forward slashes")
    pure = PurePosixPath(raw)
    if not pure.parts or pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        raise ValueError(f"{label} path must be canonical and relative")
    directory_descriptor = -1
    file_descriptor = -1
    try:
        directory_descriptor = os.open(root, _safe_open_flags(directory=True))
        for part in pure.parts[:-1]:
            next_descriptor = os.open(part, _safe_open_flags(directory=True), dir_fd=directory_descriptor)
            os.close(directory_descriptor)
            directory_descriptor = next_descriptor
        file_descriptor = os.open(pure.parts[-1], _safe_open_flags(directory=False), dir_fd=directory_descriptor)
        if not stat.S_ISREG(os.fstat(file_descriptor).st_mode):
            raise ValueError(f"{label} is not a regular file")
        descriptor, file_descriptor = file_descriptor, -1
        return descriptor, pure.as_posix()
    except ValueError:
        raise
    except (OSError, TypeError) as exc:
        raise ValueError(f"cannot open {label} safely") from exc
    finally:
        if file_descriptor != -1:
            os.close(file_descriptor)
        if directory_descriptor != -1:
            os.close(directory_descriptor)


def read_contained_text_and_hash(root: Path, value: Path | str, label: str) -> tuple[str, str, str]:
    """Read and hash one checked artifact through a bound file descriptor.

    The inode comparison closes the check-then-open race: a symlink or another
    file substituted after `safe_regular_file()` is never read as trusted input.
    """
    descriptor, relative = safe_regular_file(root, value, label)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError(f"{label} is not a regular file")
        chunks: list[bytes] = []
        digest = hashlib.sha256()
        while chunk := os.read(descriptor, 65536):
            chunks.append(chunk)
            digest.update(chunk)
        after = os.fstat(descriptor)
        if _identity(after) != _identity(before) or after.st_size != before.st_size or after.st_mtime_ns != before.st_mtime_ns:
            raise ValueError(f"{label} changed while being read")
        try:
            text = b"".join(chunks).decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"{label} is not valid UTF-8") from exc
        return text, "sha256:" + digest.hexdigest(), relative
    finally:
        os.close(descriptor)


def validate(project_root: Path, foundation: Path, artifacts: list[Path]) -> list[str]:
    """Validate artifact bindings against the Foundation's current file content."""
    errors: list[str] = []
    try:
        root = Path(project_root).resolve(strict=True)
        if not root.is_dir():
            raise ValueError("project_root is not a directory")
        foundation_text, foundation_content_hash, foundation_relative = read_contained_text_and_hash(root, foundation, "Foundation")
        foundation_meta = frontmatter(foundation_text)
    except (OSError, UnicodeError, ValueError) as exc:
        return [str(exc)]

    if foundation_meta.get("status") != "APPROVED_FOR_SPECIFICATION":
        errors.append("Foundation is not approved for specification")
    approval_fingerprint = foundation_meta.get("approval_fingerprint", "")
    if not FINGERPRINT.fullmatch(approval_fingerprint):
        errors.append("Foundation approval_fingerprint is missing or malformed")
    if not artifacts:
        errors.append("at least one downstream artifact is required")
    for artifact in artifacts:
        try:
            artifact_text, _, artifact_relative = read_contained_text_and_hash(root, artifact, "artifact")
            artifact_meta = frontmatter(artifact_text)
        except (OSError, UnicodeError, ValueError) as exc:
            errors.append(f"artifact is invalid: {artifact}: {exc}")
            continue
        if not artifact_meta.get("artifact_type"):
            errors.append(f"artifact has no artifact_type: {artifact_relative}")
        if artifact_meta.get("foundation_path") != foundation_relative:
            errors.append(f"artifact foundation_path is not the canonical Foundation path: {artifact_relative}")
        if artifact_meta.get("foundation_content_sha256") != foundation_content_hash:
            errors.append(f"artifact Foundation content hash does not match current Foundation: {artifact_relative}")
        if artifact_meta.get("foundation_approval_fingerprint") != approval_fingerprint:
            errors.append(f"artifact Foundation approval fingerprint does not match current Foundation: {artifact_relative}")

    return list(dict.fromkeys(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--foundation", type=Path, required=True)
    parser.add_argument("--artifact", type=Path, action="append", default=[])
    args = parser.parse_args()
    errors = validate(args.project_root, args.foundation, args.artifact)
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: supplied artifacts are bound by canonical frontmatter and current Foundation content")
    return 0


if __name__ == "__main__":
    sys.exit(main())
