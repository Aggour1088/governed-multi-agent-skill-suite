#!/usr/bin/env python3
"""Validate a bounded execution ledger against its active v2 work-package contract."""

from __future__ import annotations

import argparse
import json
from pathlib import PurePosixPath, Path


TASK_STATUSES = {"planned", "active", "blocked", "done", "cancelled"}
LEDGER_STATUSES = {"planned", "active", "paused", "blocked", "completed", "cancelled"}
ROLES = {"coordinator", "implementer", "tester", "reviewer", "verifier", "specialist"}


def canonical_relative_path(value: object) -> bool:
    if not isinstance(value, str) or not value.strip() or "\\" in value:
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and bool(path.parts) and all(part not in {"", ".", ".."} for part in path.parts)


def _allowed_parallel_pairs(contract: dict) -> set[frozenset[str]]:
    pairs: set[frozenset[str]] = set()
    groups = contract.get("scope", {}).get("parallel_write_groups", [])
    if not isinstance(groups, list):
        return pairs
    for group in groups:
        if isinstance(group, list) and len(group) > 1 and all(isinstance(item, str) for item in group):
            for first_index, first in enumerate(group):
                for second in group[first_index + 1 :]:
                    pairs.add(frozenset((first, second)))
    return pairs


def validate_ledger(ledger: object, contract: object) -> list[str]:
    """Return errors for a ledger that could cause drift, parallel conflict, or endless repair."""
    errors: list[str] = []
    if not isinstance(ledger, dict):
        return ["ledger must be an object"]
    if not isinstance(contract, dict):
        return ["contract must be an object"]
    if ledger.get("schema_version") != "2.0":
        errors.append("ledger.schema_version must be 2.0")
    if ledger.get("work_package_id") != contract.get("contract_id"):
        errors.append("ledger work_package_id must match contract_id")
    if ledger.get("baseline_revision") != contract.get("project", {}).get("baseline_revision"):
        errors.append("ledger baseline_revision must match the contract baseline_revision")
    if not isinstance(ledger.get("workspace_id"), str) or not ledger["workspace_id"].strip():
        errors.append("ledger.workspace_id is required")
    status = ledger.get("status")
    if status not in LEDGER_STATUSES:
        errors.append("ledger.status is invalid")
    if not isinstance(ledger.get("next_safe_action"), str) or not ledger["next_safe_action"].strip():
        errors.append("ledger.next_safe_action is required; do not resume from memory")

    limit = contract.get("economics", {}).get("fix_circuit_breaker")
    fix_round = ledger.get("fix_round")
    if not isinstance(fix_round, int) or isinstance(fix_round, bool) or fix_round < 0:
        errors.append("ledger.fix_round must be a non-negative integer")
    elif isinstance(limit, int) and fix_round > limit:
        errors.append("fix circuit breaker is exhausted; stop and escalate instead of looping")

    tasks = ledger.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        return list(dict.fromkeys(errors + ["ledger.tasks must be a non-empty list"]))
    contract_targets = set(contract.get("scope", {}).get("owned_targets", []))
    task_ids: set[str] = set()
    target_owners: dict[str, str] = {}
    allowed_parallel_pairs = _allowed_parallel_pairs(contract)
    for index, task in enumerate(tasks, start=1):
        label = f"tasks[{index}]"
        if not isinstance(task, dict):
            errors.append(f"{label} must be an object")
            continue
        identifier = task.get("id")
        if not isinstance(identifier, str) or not identifier.strip():
            errors.append(f"{label}.id is required")
            continue
        if identifier in task_ids:
            errors.append(f"{label}.id is duplicated")
        task_ids.add(identifier)
        if task.get("role") not in ROLES:
            errors.append(f"{label}.role is invalid")
        if task.get("status") not in TASK_STATUSES:
            errors.append(f"{label}.status is invalid")
        owned_targets = task.get("owned_targets")
        if not isinstance(owned_targets, list):
            errors.append(f"{label}.owned_targets must be a list")
            continue
        for target in owned_targets:
            if not canonical_relative_path(target):
                errors.append(f"{label}.owned_targets must use canonical relative paths")
                continue
            if target not in contract_targets:
                errors.append(f"{label} owns target outside contract scope: {target}")
                continue
            prior = target_owners.get(target)
            if prior and frozenset((prior, identifier)) not in allowed_parallel_pairs:
                errors.append(f"write overlap detected for {target}: {prior} and {identifier}")
            else:
                target_owners[target] = identifier
    return list(dict.fromkeys(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ledger", type=Path)
    parser.add_argument("contract", type=Path)
    args = parser.parse_args()
    try:
        ledger = json.loads(args.ledger.read_text(encoding="utf-8"))
        contract = json.loads(args.contract.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"FAIL: cannot read JSON: {exc}")
        return 1
    errors = validate_ledger(ledger, contract)
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: ledger remains within its contract, ownership, and fix-loop limits")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
