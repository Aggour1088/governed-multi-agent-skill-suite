#!/usr/bin/env python3
"""Validate the v2 adversarial-evaluation catalogue without claiming it was run."""

from __future__ import annotations

import importlib.util
import json
import re
import stat
import sys
from pathlib import Path, PurePosixPath

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
CONFIGURATION_ID_RE = re.compile(r"^[a-z][a-z0-9-]{2,63}$")
RUN_VALIDATOR_PATH = Path("skills/evaluate-governed-agent-behavior/scripts/validate_evaluation_run.py")
CONFIGURATION_FIELDS = {
    "id",
    "host",
    "model",
    "capability_profile",
    "suite_material",
    "results_directory",
    "scorecard_artifact",
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


def contained_directory(root: Path, value: object, label: str) -> tuple[Path | None, list[str]]:
    """Resolve one non-symlinked, canonical directory inside the release tree."""
    if not isinstance(value, str) or not value.strip() or "\\" in value:
        return None, [f"{label} must be a canonical relative path"]
    candidate = PurePosixPath(value)
    if candidate.is_absolute() or not candidate.parts or any(part in {"", ".", ".."} for part in candidate.parts):
        return None, [f"{label} must be a canonical relative path"]
    path = root.joinpath(*candidate.parts)
    try:
        mode = path.lstat().st_mode
        resolved = path.resolve(strict=True)
        resolved.relative_to(root.resolve(strict=True))
    except (OSError, ValueError) as exc:
        return None, [f"{label} is unavailable: {exc}"]
    if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
        return None, [f"{label} must be a contained directory"]
    return path, []


def load_run_validator(root: Path):
    path = root / RUN_VALIDATOR_PATH
    specification = importlib.util.spec_from_file_location("completed_evaluation_run_validator", path)
    if specification is None or specification.loader is None:
        raise ValueError("cannot load completed evaluation run validator")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def completed_configuration_errors(root: Path, catalogue: dict, configurations: object) -> list[str]:
    """Require a complete, one-configuration scorecard before a `passed` suite claim."""
    if not isinstance(configurations, list) or not configurations:
        return ["a passed evaluation catalogue requires at least one completed configuration"]
    try:
        validator = load_run_validator(root)
    except ValueError as exc:
        return [str(exc)]
    scenarios = {scenario["id"] for scenario in catalogue.get("scenarios", []) if isinstance(scenario, dict) and isinstance(scenario.get("id"), str)}
    seen_configurations: set[str] = set()
    errors: list[str] = []
    for index, configuration in enumerate(configurations, start=1):
        label = f"completed_configurations[{index}]"
        if not isinstance(configuration, dict) or set(configuration) != CONFIGURATION_FIELDS:
            errors.append(f"{label} must declare every completed-configuration field")
            continue
        identifier = configuration.get("id")
        if not isinstance(identifier, str) or not CONFIGURATION_ID_RE.fullmatch(identifier):
            errors.append(f"{label}.id must be a lowercase hyphenated identifier")
            continue
        if identifier in seen_configurations:
            errors.append(f"{label}.id is duplicated")
            continue
        seen_configurations.add(identifier)
        if not all(isinstance(configuration.get(field), dict) and configuration[field] for field in ("host", "model", "capability_profile", "suite_material")):
            errors.append(f"{label} requires non-empty host, model, capability_profile, and suite_material")
            continue
        results_directory, directory_errors = contained_directory(root, configuration.get("results_directory"), f"{label}.results_directory")
        errors.extend(directory_errors)
        errors.extend(result_artifact_errors(root, configuration.get("scorecard_artifact")))
        if results_directory is None:
            continue
        result_files = sorted(path for path in results_directory.glob("*.json") if path.is_file() and not path.is_symlink())
        if not result_files:
            errors.append(f"{label}.results_directory contains no completed result records")
            continue
        completed: list[dict] = []
        for result_file in result_files:
            relative = result_file.relative_to(root).as_posix()
            try:
                payload, _ = read_contained_release_file(root, relative)
                run = json.loads(payload.decode("utf-8"))
            except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
                errors.append(f"{label}: cannot read {result_file.name}: {exc}")
                continue
            for error in validator.validate_evaluation_run(run, root, catalogue=catalogue):
                errors.append(f"{label}: {result_file.name}: {error}")
            if not isinstance(run, dict):
                continue
            completed.append(run)
            for field in ("host", "model", "capability_profile", "suite_material"):
                if run.get(field) != configuration[field]:
                    errors.append(f"{label}: {result_file.name} does not match configuration {field}")
            if run.get("configuration_id") != identifier:
                errors.append(f"{label}: {result_file.name} does not match configuration id")
        scenario_counts: dict[str, int] = {}
        for run in completed:
            scenario_id = run.get("scenario_id")
            if isinstance(scenario_id, str):
                scenario_counts[scenario_id] = scenario_counts.get(scenario_id, 0) + 1
            if run.get("status") != "passed":
                errors.append(f"{label}: {scenario_id or 'unknown scenario'} is not passed")
        missing = sorted(scenarios - set(scenario_counts))
        duplicate = sorted(scenario_id for scenario_id, count in scenario_counts.items() if count != 1)
        if missing:
            errors.append(f"{label} is missing completed scenarios: {', '.join(missing)}")
        if duplicate:
            errors.append(f"{label} has duplicate completed scenarios: {', '.join(duplicate)}")
        scorecard = configuration.get("scorecard_artifact")
        if isinstance(scorecard, dict) and isinstance(scorecard.get("path"), str):
            try:
                scorecard_bytes, _ = read_contained_release_file(root, scorecard["path"])
                scorecard_text = scorecard_bytes.decode("utf-8")
            except (OSError, UnicodeError, ValueError) as exc:
                errors.append(f"{label} scorecard cannot be read: {exc}")
            else:
                if f"`{identifier}`" not in scorecard_text:
                    errors.append(f"{label} scorecard does not identify its configuration")
                if not re.search(r"(?m)^- Evaluated on: \d{4}-\d{2}-\d{2} UTC$", scorecard_text):
                    errors.append(f"{label} scorecard does not record its UTC evaluation date")
                if "## Release decision" not in scorecard_text:
                    errors.append(f"{label} scorecard does not include a release decision")
    return list(dict.fromkeys(errors))


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
        if data.get("result_artifact") is not None or data.get("completed_configurations") is not None:
            errors.append("not-run evaluation fixtures must not include a result artifact or completed configurations")
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
    if status == "passed" and not errors:
        errors.extend(completed_configuration_errors(root, data, data.get("completed_configurations")))
    elif status in {"failed", "partial"} and data.get("completed_configurations") is not None:
        errors.append("only a passed evaluation catalogue may declare completed configurations")
    return list(dict.fromkeys(errors))


def main() -> int:
    repository = Path(__file__).resolve().parents[1]
    errors = validate(repository)
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: 18 adversarial evaluation fixtures and any completed configuration evidence are structurally complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
