#!/usr/bin/env python3
"""Verify a governed evidence record against real, contained files."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from evidence_integrity import (  # noqa: E402
    FINGERPRINT,
    compute_implementation_fingerprint,
    project_root as validated_project_root,
    validate_approved_artifacts,
    validate_evidence_artifacts,
    validate_recorded_at,
)


RISK = {"Fast", "Standard", "Enhanced", "Critical"}
REQUIRED_CHECKS = {"independent-test", "independent-review"}
EXPECTED_EXECUTOR = {"independent-test": "tester", "independent-review": "reviewer"}
EXPECTED_PRINCIPAL = {"independent-test": "tester_id", "independent-review": "reviewer_id"}
INDEPENDENCE = {"separate-pass-not-independent", "host-attested-independent"}
DECLARED_PASSED_STATUS = "declared-passed"
STANDALONE_EXECUTION_PROVENANCE_BLOCK = (
    "standalone validator cannot verify whether declared command execution actually ran; "
    "it cannot accept a self-declared completed record"
)


def validate_integrity(
    data: dict,
    *,
    project_root: Path,
    max_evidence_age_hours: float = 24,
    now: datetime | None = None,
) -> list[str]:
    """Lint file integrity and declared fields without inventing execution provenance."""
    errors: list[str] = []
    try:
        root = validated_project_root(project_root)
    except ValueError as exc:
        return [str(exc)]
    if not isinstance(max_evidence_age_hours, (int, float)) or isinstance(max_evidence_age_hours, bool) or max_evidence_age_hours <= 0:
        return ["max_evidence_age_hours must be positive"]
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        return ["now must be timezone-aware"]

    if data.get("schema_version") != "2.0":
        errors.append("schema_version must be 2.0")
    for key in ("work_package_id", "risk_track", "owned_targets", "roles", "checks"):
        if not data.get(key):
            errors.append(f"missing or empty {key!r}")

    roles = data.get("roles", {})
    if not isinstance(roles, dict):
        return list(dict.fromkeys(errors + ["roles must be an object"]))
    identities = [roles.get(key, "") for key in ("implementer_id", "tester_id", "reviewer_id")]
    if any(not isinstance(value, str) or not value.strip() for value in identities):
        errors.append("implementer_id, tester_id, and reviewer_id are required")
    elif len(set(identities)) != 3:
        errors.append("implementer, tester, and reviewer identities must be distinct")

    risk = data.get("risk_track")
    if risk not in RISK:
        errors.append("risk_track is invalid")
    independence = data.get("independence_status")
    if independence not in INDEPENDENCE:
        errors.append("independence_status must be separate-pass-not-independent or host-attested-independent")
    elif independence == "host-attested-independent":
        errors.append("host attestation cannot be verified by this standalone validator")
    if risk in {"Enhanced", "Critical"}:
        errors.append(f"{risk} work requires a host-attested independent evidence path; standalone validation is insufficient")

    implementation = data.get("implementation_fingerprint", "")
    if not isinstance(implementation, str) or not FINGERPRINT.fullmatch(implementation):
        errors.append("implementation_fingerprint is missing or malformed")
    else:
        try:
            actual_implementation = compute_implementation_fingerprint(root, data.get("owned_targets"))
        except ValueError as exc:
            errors.append(f"cannot recompute implementation fingerprint: {exc}")
        else:
            if actual_implementation != implementation:
                errors.append("implementation_fingerprint does not match the current owned targets")

    if "approved_artifact_fingerprints" in data:
        errors.append("legacy approved_artifact_fingerprints are not accepted; use approved_artifacts with contained hashes")
    errors.extend(validate_approved_artifacts(root, data.get("approved_artifacts")))

    checks = data.get("checks", [])
    if not isinstance(checks, list):
        return list(dict.fromkeys(errors + ["checks must be a list"]))
    kinds = {check.get("kind") for check in checks if isinstance(check, dict)}
    missing = REQUIRED_CHECKS - kinds
    if missing:
        errors.append("missing mandatory checks: " + ", ".join(sorted(missing)))
    for check in checks:
        if not isinstance(check, dict):
            errors.append("check must be an object")
            continue
        kind = check.get("kind")
        label = kind if isinstance(kind, str) and kind else "check"
        if not isinstance(kind, str) or not kind:
            errors.append("check kind is required")
        if check.get("status") != DECLARED_PASSED_STATUS:
            errors.append(f"{label} must use status {DECLARED_PASSED_STATUS!r}; a raw record cannot claim a verified pass")
        if check.get("implementation_fingerprint") != implementation:
            errors.append(f"{label} is stale")
        if kind in REQUIRED_CHECKS:
            expected_role = EXPECTED_EXECUTOR[kind]
            expected_principal = roles.get(EXPECTED_PRINCIPAL[kind])
            if check.get("executor_role") != expected_role:
                errors.append(f"{label} must be executed by the declared {expected_role}")
            if check.get("declared_principal_id") != expected_principal:
                errors.append(f"{label} principal does not match the declared {expected_role} identity")
        command = check.get("command")
        if not isinstance(command, list) or not command or any(not isinstance(token, str) or not token.strip() for token in command):
            errors.append(f"{label} requires a structured non-empty command")
        exit_code = check.get("exit_code")
        if not isinstance(exit_code, int) or isinstance(exit_code, bool) or exit_code != 0:
            errors.append(f"{label} requires exit_code 0")
        timestamp_error = validate_recorded_at(check.get("recorded_at"), now, float(max_evidence_age_hours))
        if timestamp_error:
            errors.append(f"{label} {timestamp_error}")
        errors.extend(validate_evidence_artifacts(root, check, label))
    return list(dict.fromkeys(errors))


def validate(
    data: dict,
    *,
    project_root: Path,
    max_evidence_age_hours: float = 24,
    now: datetime | None = None,
) -> list[str]:
    """Return acceptance blockers, never a self-declared execution pass."""
    errors = validate_integrity(
        data,
        project_root=project_root,
        max_evidence_age_hours=max_evidence_age_hours,
        now=now,
    )
    errors.append(STANDALONE_EXECUTION_PROVENANCE_BLOCK)
    return list(dict.fromkeys(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--max-evidence-age-hours", type=float, default=24)
    parser.add_argument(
        "--integrity-only",
        action="store_true",
        help="lint contained files and record fields without making an acceptance decision",
    )
    args = parser.parse_args()
    try:
        data = json.loads(args.record.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("record must be a JSON object")
        validator = validate_integrity if args.integrity_only else validate
        errors = validator(
            data,
            project_root=args.project_root,
            max_evidence_age_hours=args.max_evidence_age_hours,
        )
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}")
        return 1
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    if args.integrity_only:
        print("INTEGRITY_ONLY: record fields and contained file hashes are current; command execution remains unverified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
