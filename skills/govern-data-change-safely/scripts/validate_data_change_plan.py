#!/usr/bin/env python3
"""Validate an expand-migrate-contract plan before any production data action."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path


ID_RE = re.compile(r"^[a-z][a-z0-9-]{2,63}$")
RISK_TRACKS = {"Enhanced", "Critical"}
CHANGE_CLASSES = {"additive", "destructive", "irreversible"}
RULES_DIR = Path(__file__).resolve().parents[2] / "using-governed-suite" / "scripts"
if str(RULES_DIR) not in sys.path:
    sys.path.insert(0, str(RULES_DIR))

from contract_rules import validate_contract  # noqa: E402


def non_empty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def non_empty_strings(value: object) -> bool:
    return isinstance(value, list) and bool(value) and all(non_empty_string(item) for item in value)


def validate_data_change_plan(
    plan: object, contract: object, *, now: datetime | None = None
) -> list[str]:
    """Return blockers for an unsafe data-change plan; never execute a migration."""
    errors: list[str] = []
    if not isinstance(plan, dict):
        return ["data-change plan must be an object"]
    if not isinstance(contract, dict):
        return ["contract must be an object"]
    errors.extend(f"active contract: {error}" for error in validate_contract(contract, now=now))
    if plan.get("schema_version") != "2.0":
        errors.append("schema_version must be 2.0")
    identifier = plan.get("data_change_id")
    if not isinstance(identifier, str) or not ID_RE.fullmatch(identifier):
        errors.append("data_change_id must be a lowercase hyphenated identifier")
    if plan.get("work_package_id") != contract.get("contract_id"):
        errors.append("work_package_id must match the active contract")
    risk = plan.get("risk_track")
    if risk not in RISK_TRACKS:
        errors.append("data-change risk_track must be Enhanced or Critical")
    if risk != contract.get("risk_track"):
        errors.append("data-change risk_track must match the active contract")
    if not isinstance(plan.get("production_data"), bool):
        errors.append("production_data must be boolean")
    change_class = plan.get("change_class")
    if change_class not in CHANGE_CLASSES:
        errors.append("change_class must be additive, destructive, or irreversible")
    if not non_empty_strings(plan.get("affected_objects")):
        errors.append("affected_objects must be a non-empty string list")
    if plan.get("production_data"):
        if not non_empty_strings(contract.get("scope", {}).get("database_objects")):
            errors.append("production data change requires declared contract scope.database_objects")
        if contract.get("authority", {}).get("production_action") not in {"owner-authorized", "ci-protected"}:
            errors.append("production data change requires owner-authorized or ci-protected production authority")
        if not non_empty_string(plan.get("data_window")):
            errors.append("production data change requires a bounded data_window")

    expand = plan.get("expand")
    if not isinstance(expand, dict) or not non_empty_strings(expand.get("steps")):
        errors.append("expand.steps must be a non-empty string list")
    backfill = plan.get("backfill")
    if not isinstance(backfill, dict):
        errors.append("backfill must be an object")
    else:
        if plan.get("production_data") and backfill.get("idempotent") is not True:
            errors.append("production data backfill must be idempotent")
        if plan.get("production_data") and backfill.get("resumable") is not True:
            errors.append("production data backfill must be resumable")
        if plan.get("production_data"):
            if not isinstance(backfill.get("batch_size"), int) or isinstance(backfill.get("batch_size"), bool) or backfill["batch_size"] <= 0:
                errors.append("production data backfill requires a positive batch_size")
            if not non_empty_string(backfill.get("progress_record")):
                errors.append("production data backfill requires a progress_record")
    validate = plan.get("validate")
    if not isinstance(validate, dict):
        errors.append("validate must be an object")
    else:
        if not non_empty_strings(validate.get("queries")):
            errors.append("validate.queries must be a non-empty string list")
        if not non_empty_strings(validate.get("invariants")):
            errors.append("validate.invariants must be a non-empty string list")
    cutover = plan.get("cutover")
    if not isinstance(cutover, dict) or not non_empty_strings(cutover.get("deployment_order")):
        errors.append("cutover.deployment_order must be a non-empty string list")
    observe = plan.get("observe")
    if not isinstance(observe, dict):
        errors.append("observe must be an object")
    else:
        if not non_empty_string(observe.get("period")):
            errors.append("observe.period is required")
        if not non_empty_strings(observe.get("signals")):
            errors.append("observe.signals must be a non-empty string list")
    contract_stage = plan.get("contract")
    if not isinstance(contract_stage, dict) or contract_stage.get("after_observation") is not True:
        errors.append("contract.after_observation must be true")

    recovery = plan.get("recovery")
    requires_recovery = bool(plan.get("production_data")) or change_class in {"destructive", "irreversible"}
    if requires_recovery:
        if not isinstance(recovery, dict):
            errors.extend(["backup and restore proof is required", "recovery plan is required"])
        else:
            if not non_empty_string(recovery.get("backup_reference")):
                errors.append("backup_reference is required")
            if not non_empty_string(recovery.get("restore_drill")):
                errors.append("restore_drill is required")
            if recovery.get("strategy") not in {"rollback", "forward-recovery", "both"}:
                errors.append("recovery.strategy must be rollback, forward-recovery, or both")
            if not non_empty_string(recovery.get("pause_resume")):
                errors.append("recovery.pause_resume is required")
    return list(dict.fromkeys(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("contract", type=Path)
    args = parser.parse_args()
    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        contract = json.loads(args.contract.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"FAIL: cannot read JSON: {exc}")
        return 1
    errors = validate_data_change_plan(plan, contract)
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: data-change plan contains required compatibility, recovery, and observation controls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
