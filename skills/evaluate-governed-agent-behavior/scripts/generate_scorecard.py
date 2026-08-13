#!/usr/bin/env python3
"""Generate a transparent Markdown scorecard from validated evaluation-run JSON files."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from validate_evaluation_run import load_catalogue, scenario_index, validate_evaluation_run


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--catalogue", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
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
    counts = Counter(row["status"] for row in rows)
    scenarios, scenario_errors = scenario_index(catalogue)
    if scenario_errors:
        print("FAIL")
        for error in scenario_errors:
            print(f"- {error}")
        return 1
    completed_scenarios = {row["scenario_id"] for row in rows}
    not_run_scenarios = sorted(set(scenarios) - completed_scenarios)
    lines = [
        "# Governed Agent Behavior Scorecard",
        "",
        "This scorecard summarizes validated raw result records. It does not imply that unlisted hosts or scenarios passed.",
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
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"WROTE: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
