#!/usr/bin/env python3
"""Fail-closed integrity helpers bundled with a standalone governance skill."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath


FINGERPRINT = re.compile(r"^sha256:[0-9a-f]{64}$")
UTC_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$")


def project_root(path: Path) -> Path:
    """Return an existing directory chosen explicitly by the caller."""
    try:
        root = Path(path).resolve(strict=True)
    except OSError as exc:
        raise ValueError(f"cannot resolve project_root: {exc}") from exc
    if not root.is_dir():
        raise ValueError("project_root must be an existing directory")
    return root


def canonical_relative_path(value: object) -> tuple[str, tuple[str, ...]]:
    """Reject absolute, traversal, and platform-ambiguous evidence paths."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("path must be a non-empty string")
    if "\\" in value:
        raise ValueError("path must use forward slashes")
    candidate = PurePosixPath(value)
    parts = candidate.parts
    if not parts or candidate.is_absolute() or any(part in {"", ".", ".."} for part in parts):
        raise ValueError("path must be canonical and relative")
    return candidate.as_posix(), parts


def _safe_open_flags(*, directory: bool) -> int:
    """Return the POSIX-only flags needed for descriptor-bound traversal."""
    if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
        raise ValueError("safe contained evidence hashing requires POSIX O_NOFOLLOW, O_DIRECTORY, and dir_fd support")
    flags = os.O_RDONLY | os.O_NOFOLLOW
    if directory:
        flags |= os.O_DIRECTORY
    elif hasattr(os, "O_NONBLOCK"):
        flags |= os.O_NONBLOCK
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    return flags


def contained_regular_file(root: Path, value: object) -> tuple[int, str]:
    """Open one contained regular file through descriptor-bound directory traversal.

    Each path component is opened relative to an already-open parent directory.
    This prevents a symlinked parent directory from redirecting the final read after
    the caller has selected the project root.
    """
    root = project_root(root)
    relative, parts = canonical_relative_path(value)
    directory_descriptor = -1
    file_descriptor = -1
    try:
        directory_descriptor = os.open(root, _safe_open_flags(directory=True))
        for part in parts[:-1]:
            next_descriptor = os.open(part, _safe_open_flags(directory=True), dir_fd=directory_descriptor)
            os.close(directory_descriptor)
            directory_descriptor = next_descriptor
        file_descriptor = os.open(parts[-1], _safe_open_flags(directory=False), dir_fd=directory_descriptor)
        if not stat.S_ISREG(os.fstat(file_descriptor).st_mode):
            raise ValueError(f"referenced path is not a regular file: {relative}")
        descriptor, file_descriptor = file_descriptor, -1
        return descriptor, relative
    except ValueError:
        raise
    except (OSError, TypeError) as exc:
        raise ValueError(f"cannot open referenced path safely: {relative}") from exc
    finally:
        if file_descriptor != -1:
            os.close(file_descriptor)
        if directory_descriptor != -1:
            os.close(directory_descriptor)


def _identity(info: os.stat_result) -> tuple[int, int, int]:
    return info.st_dev, info.st_ino, stat.S_IFMT(info.st_mode)


def _hash_open_descriptor(descriptor: int, relative: str) -> str:
    """Hash an already-open, descriptor-bound regular file."""
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError(f"referenced path is not a regular file: {relative}")
        digest = hashlib.sha256()
        while chunk := os.read(descriptor, 65536):
            digest.update(chunk)
        after = os.fstat(descriptor)
        if _identity(after) != _identity(before) or after.st_size != before.st_size or after.st_mtime_ns != before.st_mtime_ns:
            raise ValueError(f"referenced file changed while being hashed: {relative}")
        return "sha256:" + digest.hexdigest()
    finally:
        os.close(descriptor)


def sha256_contained_file(root: Path, value: object) -> tuple[str, str]:
    """Hash one contained regular file without reopening a path by name."""
    descriptor, relative = contained_regular_file(root, value)
    return _hash_open_descriptor(descriptor, relative), relative


def compute_implementation_fingerprint(root: Path, owned_targets: object) -> str:
    """Hash the current declared owned files using canonical JSON."""
    if not isinstance(owned_targets, list) or not owned_targets:
        raise ValueError("owned_targets must be a non-empty list")
    files: list[dict[str, str]] = []
    seen: set[str] = set()
    for target in owned_targets:
        digest, relative = sha256_contained_file(root, target)
        if relative in seen:
            raise ValueError(f"owned_targets contains a duplicate path: {relative}")
        seen.add(relative)
        files.append({"path": relative, "sha256": digest})
    encoded = json.dumps({"files": sorted(files, key=lambda item: item["path"])}, separators=(",", ":"), sort_keys=True)
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def validate_artifact_reference(root: Path, item: object, label: str) -> list[str]:
    if not isinstance(item, dict):
        return [f"{label} must be an object"]
    expected = item.get("sha256")
    if not isinstance(expected, str) or not FINGERPRINT.fullmatch(expected):
        return [f"{label} has an invalid sha256"]
    try:
        actual, _ = sha256_contained_file(root, item.get("path"))
    except ValueError as exc:
        return [f"{label} is invalid: {exc}"]
    if actual != expected:
        return [f"{label} hash does not match the current file"]
    return []


def validate_approved_artifacts(root: Path, value: object) -> list[str]:
    if not isinstance(value, list) or not value:
        return ["approved_artifacts must be a non-empty list of hashed file references"]
    errors: list[str] = []
    identifiers: set[str] = set()
    for index, artifact in enumerate(value):
        if not isinstance(artifact, dict):
            errors.append("approved artifact must be an object")
            continue
        identifier = artifact.get("id")
        if not isinstance(identifier, str) or not identifier.strip():
            errors.append(f"approved artifact {index} has no id")
        elif identifier in identifiers:
            errors.append(f"approved artifact id is duplicated: {identifier}")
        else:
            identifiers.add(identifier)
        errors.extend(validate_artifact_reference(root, artifact, f"approved artifact {identifier or index}"))
    return errors


def validate_evidence_artifacts(root: Path, check: dict, label: str) -> list[str]:
    artifacts = check.get("evidence_artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        return [f"{label} requires non-empty evidence_artifacts; free-text raw_evidence is not accepted"]
    errors: list[str] = []
    for index, artifact in enumerate(artifacts):
        errors.extend(validate_artifact_reference(root, artifact, f"{label} evidence artifact {index}"))
    return errors


def validate_recorded_at(value: object, now: datetime, max_age_hours: float) -> str | None:
    if not isinstance(value, str) or not UTC_TIMESTAMP.fullmatch(value):
        return "timestamp must be an RFC 3339 UTC value ending in Z"
    try:
        recorded_at = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return "timestamp cannot be parsed"
    if recorded_at > now + timedelta(minutes=5):
        return "timestamp is implausibly in the future"
    if now - recorded_at > timedelta(hours=max_age_hours):
        return f"timestamp is older than the {max_age_hours:g}-hour freshness window"
    return None
