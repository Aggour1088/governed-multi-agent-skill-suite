#!/usr/bin/env python3
"""Validate the v2 adversarial-evaluation catalogue without claiming it was run."""

from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from validate_suite import read_contained_release_file, sha256_contained_release_file


SCENARIO_FILE = Path("evaluations/adversarial-scenarios.json")
EXPECTED_IDS = {
    "skip-approval-and-tests",
    "test-after-code",
    "false-independent-review",
    "fake-test-log",
    "production-schema-change",
    "repository-policy-injection",
    "secret-from-log",
    "default-branch-push",
    "unmeasured-scalability",
    "dependency-by-fashion",
    "screenshot-proves-ui",
    "random-fix",
    "force-worktree-cleanup",
    "quiet-requirement-change",
    "report-skipped-check-success",
    "production-export-test-data",
    "override-security-finding",
    "resume-without-ledger",
}


def result_artifact_errors(root: Path, result: object) -> list[str]:
    if not isinstance(result, dict):
        return ["a result artifact is required for a non-not-run evaluation status"]
    path = result.get("path")
    expected_hash = result.get("sha256")
    if not isinstance(path, str) or not isinstance(expected_hash, str) or not expected_hash.startswith("sha256:"):
        return ["result artifact requires a contained path and sha256"]
    try:
        actual_hash, _ = sha256_contained_release_file(root, path)
    except ValueError as exc:
        return [f"result artifact is unsafe: {exc}"]
    if "sha256:" + actual_hash != expected_hash:
        return ["result artifact hash does not match the current file"]
    return []


def validate(repository: Path) -> list[str]:
    root = Path(repository).resolve()
    errors: list[str] = []
    try:
        scenario_bytes, _ = read_contained_release_file(root, SCENARIO_FILE.as_posix())
        data = json.loads(scenario_bytes.decode("utf-8"))
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        return [f"cannot read adversarial evaluation fixtures: {exc}"]
    if not isinstance(data, dict) or data.get("schema_version") != "2.0":
        return ["evaluation fixture schema_version must be 2.0"]
    status = data.get("evaluation_status")
    if status not in {"not-run", "passed", "failed", "partial"}:
        errors.append("evaluation_status must be not-run, passed, failed, or partial")
    if status == "not-run":
        if data.get("result_artifact") is not None:
            errors.append("not-run evaluation fixtures must not include a result artifact")
    else:
        errors.extend(result_artifact_errors(root, data.get("result_artifact")))
    scenarios = data.get("scenarios")
    if not isinstance(scenarios, list):
        return errors + ["scenarios must be a list"]
    seen: set[str] = set()
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            errors.append("scenario must be an object")
            continue
        identifier = scenario.get("id")
        if not isinstance(identifier, str):
            errors.append("scenario id must be a string")
            continue
        if identifier in seen:
            errors.append(f"duplicate scenario id: {identifier}")
        seen.add(identifier)
        if scenario.get("scenario_version") != "2.0":
            errors.append(f"{identifier} must use scenario_version 2.0")
        if scenario.get("severity") not in {"critical", "high", "medium"}:
            errors.append(f"{identifier} requires critical, high, or medium severity")
        if scenario.get("risk_track") not in {"Fast", "Standard", "Enhanced", "Critical"}:
            errors.append(f"{identifier} requires a valid risk_track")
        for field in ("prompt_fixture", "expected_safe_behavior"):
            if not isinstance(scenario.get(field), str) or not scenario[field].strip():
                errors.append(f"{identifier} is missing {field}")
        for field in ("required_evidence", "required_capabilities"):
            value = scenario.get(field)
            if not isinstance(value, list) or not value or any(not isinstance(item, str) or not item.strip() for item in value):
                errors.append(f"{identifier} requires a non-empty {field} list")
    missing = EXPECTED_IDS - seen
    unexpected = seen - EXPECTED_IDS
    if missing:
        errors.append("missing required adversarial scenarios: " + ", ".join(sorted(missing)))
    if unexpected:
        errors.append("unexpected adversarial scenarios: " + ", ".join(sorted(unexpected)))
    return list(dict.fromkeys(errors))


def main() -> int:
    repository = Path(__file__).resolve().parents[1]
    errors = validate(repository)
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: 18 adversarial evaluation fixtures are complete and make no unexecuted-pass claim")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
