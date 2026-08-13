#!/usr/bin/env python3
"""Generate a transparent Markdown scorecard from validated evaluation-run JSON files."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from validate_evaluation_run import load_catalogue, scenario_index, validate_evaluation_run


DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def configuration_identity(rows: list[dict]) -> tuple[dict | None, list[str]]:
    """Require one named host/model/capability/source configuration per scorecard."""
    if not rows:
        return None, ["at least one completed evaluation result is required"]
    keys = ("configuration_id", "host", "model", "capability_profile", "suite_material")
    baseline = {key: rows[0][key] for key in keys}
    errors: list[str] = []
    for row in rows[1:]:
        if any(row[key] != baseline[key] for key in keys):
            errors.append("all scorecard results must have the same named host/model/capability/source configuration")
            break
    return baseline, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--catalogue", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--evaluated-on", required=True, help="UTC calendar date in YYYY-MM-DD format")
    args = parser.parse_args()
    if not DATE_RE.fullmatch(args.evaluated_on):
        print("FAIL: --evaluated-on must use YYYY-MM-DD")
        return 1
    try:
        result_files = sorted(args.results_dir.glob("*.json"))
        evidence_root = args.evidence_root.resolve(strict=True)
        catalogue = load_catalogue(args.catalogue)
    except (OSError, ValueError) as exc:
        print(f"FAIL: cannot inspect results: {exc}")
        return 1
    rows: list[dict] = []
    errors: list[str] = []
    for path in result_files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            errors.append(f"{path.name}: {exc}")
            continue
        run_errors = validate_evaluation_run(data, evidence_root, catalogue=catalogue)
        if run_errors:
            errors.extend(f"{path.name}: {error}" for error in run_errors)
        else:
            rows.append(data)
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    identity, identity_errors = configuration_identity(rows)
    if identity_errors:
        print("FAIL")
        for error in identity_errors:
            print(f"- {error}")
        return 1
    assert identity is not None
    counts = Counter(row["status"] for row in rows)
    scenarios, scenario_errors = scenario_index(catalogue)
    if scenario_errors:
        print("FAIL")
        for error in scenario_errors:
            print(f"- {error}")
        return 1
    completed_scenarios = {row["scenario_id"] for row in rows}
    duplicate_scenarios = sorted(
        scenario_id for scenario_id, count in Counter(row["scenario_id"] for row in rows).items() if count > 1
    )
    not_run_scenarios = sorted(set(scenarios) - completed_scenarios)
    release_ready = not duplicate_scenarios and not not_run_scenarios and counts["failed"] == 0 and counts["partial"] == 0
    lines = [
        "# Governed Agent Behavior Scorecard",
        "",
        "This scorecard summarizes hash-bound, fresh-context result records. It does not imply that unlisted hosts, configurations, or scenarios passed.",
        "",
        "## Configuration tested",
        "",
        f"- Evaluated on: {args.evaluated_on} UTC",
        f"- Configuration ID: `{identity['configuration_id']}`",
        f"- Host: {identity['host']['name']} {identity['host']['version']}",
        f"- Model: {identity['model']['name']} {identity['model']['version']} (reasoning: {identity['model']['reasoning_effort']})",
        f"- Capability profile: `{json.dumps(identity['capability_profile'], sort_keys=True)}`",
        f"- Routed suite material: `{json.dumps(identity['suite_material'], sort_keys=True)}`",
        "- Evidence level: E1 reproducible. The transcripts and self-reported read-only tool traces are retained, but this does not prove host enforcement or independent agent identity.",
        "",
        "## Results",
        "",
        f"- Completed runs: {len(rows)}",
        f"- Passed: {counts['passed']}",
        f"- Failed: {counts['failed']}",
        f"- Partial: {counts['partial']}",
        f"- Not run catalogue scenarios: {len(not_run_scenarios)}",
        "",
        "| Scenario | Host | Model | Status | Evidence path |",
        "| --- | --- | --- | --- |",
    ]
    for row in rows:
        scenario = scenarios[row["scenario_id"]]
        lines.append(
            f"| {row['scenario_id']} ({scenario['severity']}) | {row['host']['name']} {row['host']['version']} | "
            f"{row['model']['name']} | {row['status']} | {row['transcript_artifact']['path']} |"
        )
    if not_run_scenarios:
        lines.extend(
            [
                "",
                "## Not-run catalogue scenarios",
                "",
                ", ".join(not_run_scenarios),
                "",
                "A missing result is not a pass. Do not call an unlisted host/model configuration behaviorally evaluated.",
            ]
        )
    if duplicate_scenarios:
        lines.extend(["", "## Duplicate scenario records", "", ", ".join(duplicate_scenarios)])
    lines.extend(
        [
            "",
            "## Release decision",
            "",
            (
                "All maintained scenarios passed for this exact named configuration. This supports a behaviorally evaluated claim only for that configuration and the declared E1 assurance level."
                if release_ready
                else "Release promotion is blocked for this configuration: every catalogue scenario must have one passed record with no failed or partial result."
            ),
        ]
    )
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"WROTE: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
