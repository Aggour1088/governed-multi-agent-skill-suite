#!/usr/bin/env python3
"""Validate a completed fresh-context behavior evaluation and its raw artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import stat
import sys
from pathlib import Path, PurePosixPath
import re


RULES_DIR = Path(__file__).resolve().parents[2] / "using-governed-suite" / "scripts"
if str(RULES_DIR) not in sys.path:
    sys.path.insert(0, str(RULES_DIR))

from contract_rules import CAPABILITY_VALUES  # noqa: E402


CAPABILITY_FIELDS = {
    "skill_routing",
    "tool_mediation",
    "agent_identity",
    "workspace_isolation",
    "test_evidence",
    "browser_verification",
    "ci_cd_integration",
    "secret_boundary",
    "production_control",
}
STATUSES_TO_GRADES = {"passed": "pass", "failed": "fail", "partial": "partial"}
CONFIGURATION_ID_RE = re.compile(r"^[a-z][a-z0-9-]{2,63}$")
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
SUITE_MATERIAL_FIELDS = {
    "router_sha256",
    "routing_policy_sha256",
    "source_policy_sha256",
}


def contained_file(root: Path, descriptor: object, label: str) -> list[str]:
    if not isinstance(descriptor, dict):
        return [f"{label} artifact is required"]
    path_value = descriptor.get("path")
    expected = descriptor.get("sha256")
    if not isinstance(path_value, str) or not path_value.strip() or "\\" in path_value:
        return [f"{label} artifact path must be a canonical relative path"]
    candidate = PurePosixPath(path_value)
    if candidate.is_absolute() or not candidate.parts or any(part in {"", ".", ".."} for part in candidate.parts):
        return [f"{label} artifact path must be a canonical relative path"]
    path = root.joinpath(*candidate.parts)
    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to(root.resolve(strict=True))
        mode = path.lstat().st_mode
    except (OSError, ValueError) as exc:
        return [f"{label} artifact is unavailable: {exc}"]
    if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
        return [f"{label} artifact must be a contained regular file"]
    actual = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    if not isinstance(expected, str) or actual != expected:
        return [f"{label} artifact hash does not match"]
    return []


def scenario_index(catalogue: object) -> tuple[dict[str, dict], list[str]]:
    """Return a unique scenario index for an already-validated catalogue."""
    if not isinstance(catalogue, dict) or catalogue.get("schema_version") != "2.0":
        return {}, ["evaluation catalogue must be a schema_version 2.0 object"]
    scenarios = catalogue.get("scenarios")
    if not isinstance(scenarios, list):
        return {}, ["evaluation catalogue scenarios must be a list"]
    indexed: dict[str, dict] = {}
    errors: list[str] = []
    for scenario in scenarios:
        if not isinstance(scenario, dict) or not isinstance(scenario.get("id"), str) or not scenario["id"].strip():
            errors.append("evaluation catalogue has an invalid scenario id")
            continue
        if scenario["id"] in indexed:
            errors.append(f"evaluation catalogue duplicates scenario id: {scenario['id']}")
            continue
        indexed[scenario["id"]] = scenario
    return indexed, errors


def load_catalogue(path: Path) -> dict:
    try:
        raw = Path(path).read_text(encoding="utf-8")
        catalogue = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read evaluation catalogue: {exc}") from exc
    _, errors = scenario_index(catalogue)
    if errors:
        raise ValueError("invalid evaluation catalogue: " + "; ".join(errors))
    return catalogue


def validate_evaluation_run(
    data: object, root: Path, *, catalogue: object | None = None
) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["evaluation run must be an object"]
    if data.get("schema_version") != "2.0":
        errors.append("schema_version must be 2.0")
    for field in ("run_id", "scenario_id", "scenario_version"):
        if not isinstance(data.get(field), str) or not data[field].strip():
            errors.append(f"{field} is required")
    if not isinstance(data.get("configuration_id"), str) or not CONFIGURATION_ID_RE.fullmatch(data["configuration_id"]):
        errors.append("configuration_id must be a lowercase hyphenated identifier")
    if data.get("scenario_severity") not in {"critical", "high", "medium", "low"}:
        errors.append("scenario_severity must be critical, high, medium, or low")
    if catalogue is not None:
        indexed, catalogue_errors = scenario_index(catalogue)
        errors.extend(catalogue_errors)
        scenario = indexed.get(data.get("scenario_id")) if isinstance(data.get("scenario_id"), str) else None
        if scenario is None:
            errors.append("scenario_id is not present in the evaluation catalogue")
        else:
            if data.get("scenario_version") != scenario.get("scenario_version"):
                errors.append("scenario_version does not match the evaluation catalogue")
            if data.get("scenario_severity") != scenario.get("severity"):
                errors.append("scenario_severity does not match the evaluation catalogue")
    if data.get("status") not in {"passed", "failed", "partial"}:
        errors.append("status must be passed, failed, or partial; not-run is not a completed result")
    for field in ("host", "model"):
        value = data.get(field)
        if not isinstance(value, dict) or not isinstance(value.get("name"), str) or not value["name"].strip() or not isinstance(value.get("version"), str) or not value["version"].strip():
            errors.append(f"{field} requires non-empty name and version")
    model = data.get("model")
    if isinstance(model, dict) and (not isinstance(model.get("reasoning_effort"), str) or not model["reasoning_effort"].strip()):
        errors.append("model.reasoning_effort is required")
    configuration = data.get("configuration")
    if not isinstance(configuration, dict) or not configuration:
        errors.append("configuration must be a non-empty object describing the host/model run")
    suite_material = data.get("suite_material")
    if not isinstance(suite_material, dict) or set(suite_material) != SUITE_MATERIAL_FIELDS:
        errors.append("suite_material must declare every routed source fingerprint")
    elif any(not isinstance(suite_material[field], str) or not SHA256_RE.fullmatch(suite_material[field]) for field in SUITE_MATERIAL_FIELDS):
        errors.append("suite_material fingerprints must be sha256 values")
    capabilities = data.get("capability_profile")
    if not isinstance(capabilities, dict) or set(capabilities) != CAPABILITY_FIELDS:
        errors.append("capability_profile must declare every v2 capability")
    elif any(capabilities[field] not in allowed for field, allowed in CAPABILITY_VALUES.items()):
        errors.append("capability_profile contains an unsupported v2 capability value")
    result = data.get("result")
    if not isinstance(result, dict) or result.get("grade") not in {"pass", "fail", "partial"} or not isinstance(result.get("rationale"), str) or not result["rationale"].strip():
        errors.append("result requires a pass/fail/partial grade and rationale")
    if isinstance(result, dict) and data.get("status") in STATUSES_TO_GRADES:
        expected_grade = STATUSES_TO_GRADES[data["status"]]
        if result.get("grade") != expected_grade:
            errors.append(f"a {data['status']} status requires a {expected_grade} grade")
    errors.extend(contained_file(root, data.get("prompt_artifact"), "prompt"))
    errors.extend(contained_file(root, data.get("transcript_artifact"), "transcript"))
    errors.extend(contained_file(root, data.get("tool_trace_artifact"), "tool trace"))
    return list(dict.fromkeys(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--catalogue", type=Path, required=True)
    args = parser.parse_args()
    try:
        root = args.evidence_root.resolve(strict=True)
        if not root.is_dir():
            raise ValueError("evidence-root must be a directory")
        data = json.loads(args.run.read_text(encoding="utf-8"))
        catalogue = load_catalogue(args.catalogue)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"FAIL: cannot read evaluation result: {exc}")
        return 1
    errors = validate_evaluation_run(data, root, catalogue=catalogue)
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: evaluation run has raw, hash-bound evidence; host trust limits still apply")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
