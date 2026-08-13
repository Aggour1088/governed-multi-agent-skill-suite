#!/usr/bin/env python3
"""Run one contract-allowlisted command and emit a redacted, hash-bound evidence receipt.

The local mode creates E1 reproducible evidence. The --host-controlled mode can
create a signed E2 receipt only when the host, not the agent, protects the HMAC
key and evidence store. The program cannot establish that external condition.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import re
import stat
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path


REDACTION_PATTERNS = (
    re.compile(rb"(?i)\b(api[_-]?key|access[_-]?token|token|password|passwd|secret)\s*[:=]\s*([^\s'\"]+)"),
    re.compile(rb"(?i)\bauthorization:\s*bearer\s+([^\s'\"]+)"),
)


def fail(message: str) -> int:
    print(f"FAIL: {message}", file=sys.stderr)
    return 1


def sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def contained_relative_path(value: object) -> bool:
    if not isinstance(value, str) or not value.strip() or "\\" in value:
        return False
    candidate = Path(value)
    return not candidate.is_absolute() and all(part not in {"", ".", ".."} for part in candidate.parts)


def regular_directory(path: Path, *, create: bool = False) -> Path:
    if create and not path.exists():
        parent = path.parent.resolve(strict=True)
        if path.parent.is_symlink() or not parent.is_dir():
            raise ValueError("evidence-store parent must be a regular existing directory")
        path.mkdir(mode=0o700)
    resolved = path.resolve(strict=True)
    mode = path.lstat().st_mode
    if path.is_symlink() or not stat.S_ISDIR(mode):
        raise ValueError("path must be a regular directory")
    return resolved


def ensure_outside(candidate: Path, protected: Path) -> None:
    try:
        candidate.relative_to(protected)
    except ValueError:
        return
    raise ValueError("evidence store must be outside the project root")


def load_contract(path: Path) -> tuple[dict, str]:
    try:
        resolved = path.resolve(strict=True)
        mode = path.lstat().st_mode
    except OSError as exc:
        raise ValueError(f"cannot inspect contract: {exc}") from exc
    if path.is_symlink() or not stat.S_ISREG(mode):
        raise ValueError("contract must be a regular file")
    try:
        raw = resolved.read_bytes()
        data = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read contract JSON: {exc}") from exc
    rules_dir = Path(__file__).resolve().parents[2] / "skills" / "using-governed-suite" / "scripts"
    if not rules_dir.is_dir():
        raise ValueError("using-governed-suite contract rules are unavailable")
    if str(rules_dir) not in sys.path:
        sys.path.insert(0, str(rules_dir))
    from contract_rules import validate_contract  # noqa: PLC0415

    errors = validate_contract(data)
    if errors:
        raise ValueError("invalid contract: " + "; ".join(errors))
    return data, sha256_bytes(raw)


def git_revision(project_root: Path, revision: str) -> None:
    check = subprocess.run(
        ["git", "-C", str(project_root), "cat-file", "-e", f"{revision}^{{commit}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if check.returncode:
        raise ValueError("contract baseline_revision is unavailable in the project repository")


def current_revision(project_root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(project_root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise ValueError("project_root must be a Git repository with a current revision")
    return result.stdout.strip()


def selected_command(contract: dict, command_id: str) -> dict:
    for command in contract["authority"]["allowed_commands"]:
        if command.get("id") == command_id:
            return command
    raise ValueError("command id is not allowed by the active contract")


def safe_cwd(project_root: Path, value: object) -> Path:
    if value == ".":
        return project_root
    if not contained_relative_path(value):
        raise ValueError("contract command cwd is unsafe")
    target = (project_root / str(value)).resolve(strict=True)
    try:
        target.relative_to(project_root)
    except ValueError as exc:
        raise ValueError("contract command cwd escapes project root") from exc
    if not target.is_dir():
        raise ValueError("contract command cwd is not a directory")
    return target


def redact(value: bytes) -> bytes:
    redacted = value
    for pattern in REDACTION_PATTERNS:
        if pattern.pattern.lower().startswith(b"(?i)\\bauthorization"):
            redacted = pattern.sub(b"Authorization: Bearer [REDACTED]", redacted)
        else:
            redacted = pattern.sub(lambda match: match.group(1) + b"=[REDACTED]", redacted)
    return redacted


def write_new(path: Path, content: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = -1
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
    finally:
        if descriptor != -1:
            os.close(descriptor)


def sign_receipt(receipt: dict, key: bytes, key_id: str) -> dict:
    unsigned = dict(receipt)
    digest = hmac.new(key, canonical_json(unsigned), hashlib.sha256).hexdigest()
    signed = dict(unsigned)
    signed["signature"] = {"algorithm": "hmac-sha256", "key_id": key_id, "value": digest}
    return signed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--evidence-store", type=Path, required=True)
    parser.add_argument("--command-id", required=True)
    parser.add_argument("--host-controlled", action="store_true")
    parser.add_argument("--hmac-key-env")
    parser.add_argument("--key-id")
    args = parser.parse_args()
    try:
        project_root = regular_directory(args.project_root)
        requested_store = args.evidence_store.absolute()
        ensure_outside(requested_store.resolve(strict=False), project_root)
        evidence_store = regular_directory(requested_store, create=True)
        ensure_outside(evidence_store, project_root)
        contract, contract_hash = load_contract(args.contract)
        if contract.get("status") != "active" or not contract["authority"].get("mutation_allowed"):
            raise ValueError("active mutation-authorized contract is required")
        git_revision(project_root, contract["project"]["baseline_revision"])
        command = selected_command(contract, args.command_id)
        cwd = safe_cwd(project_root, command.get("cwd"))
        key: bytes | None = None
        if args.host_controlled:
            if not args.hmac_key_env or not args.key_id:
                raise ValueError("host-controlled receipt requires --hmac-key-env and --key-id")
            raw_key = os.environ.get(args.hmac_key_env)
            if not raw_key:
                raise ValueError("host-controlled receipt requires a non-empty host-injected HMAC key")
            key = raw_key.encode("utf-8")
    except (OSError, ValueError) as exc:
        return fail(str(exc))

    started = time.monotonic()
    try:
        result = subprocess.run(
            command["argv"],
            cwd=cwd,
            capture_output=True,
            timeout=command["timeout_seconds"],
            check=False,
        )
        stdout = result.stdout
        stderr = result.stderr
        exit_code = result.returncode
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or b""
        stderr = (exc.stderr or b"") + b"\n[runner] command timed out\n"
        exit_code = 124
        timed_out = True
    duration_ms = round((time.monotonic() - started) * 1000)
    combined_output = b"--- stdout ---\n" + redact(stdout) + b"\n--- stderr ---\n" + redact(stderr)
    receipt_id = str(uuid.uuid4())
    output_name = f"{receipt_id}.output.txt"
    receipt_name = f"{receipt_id}.receipt.json"
    try:
        write_new(evidence_store / output_name, combined_output)
        receipt = {
            "schema_version": "2.0",
            "receipt_id": receipt_id,
            "issued_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "evidence_level": "E2" if key else "E1",
            "evidence_limit": (
                "E2 applies only when the host controls this runner, HMAC key, and evidence store outside the agent authority."
                if key
                else "Local wrapper execution is reproducible evidence only; it is not independent host attestation."
            ),
            "contract_id": contract["contract_id"],
            "contract_sha256": contract_hash,
            "baseline_revision": contract["project"]["baseline_revision"],
            "project_revision": current_revision(project_root),
            "command": {"id": command["id"], "argv": command["argv"], "cwd": command["cwd"], "timeout_seconds": command["timeout_seconds"]},
            "exit_code": exit_code,
            "timed_out": timed_out,
            "duration_ms": duration_ms,
            "output_artifact": {"path": output_name, "sha256": sha256_bytes(combined_output)},
        }
        if key:
            receipt = sign_receipt(receipt, key, args.key_id)
        write_new(evidence_store / receipt_name, canonical_json(receipt) + b"\n")
    except OSError as exc:
        return fail(f"cannot write receipt: {exc}")
    receipt_path = evidence_store / receipt_name
    print(receipt_path)
    return 0 if exit_code == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
