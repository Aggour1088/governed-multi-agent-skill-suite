"""Shared, fail-closed validation rules for v2 governed work-package contracts."""

from __future__ import annotations

import json
import re
import stat
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath


CONTRACT_SCHEMA_VERSION = "2.0"
RISK_TRACKS = {"Fast", "Standard", "Enhanced", "Critical"}
LIFECYCLE_STATES = {
    "INTAKE",
    "FOUNDATION",
    "EXPERIENCE",
    "SPECIFICATION",
    "ARCHITECTURE",
    "PLAN",
    "ARTIFACT-GATE",
    "PREFLIGHT",
    "IMPLEMENT",
    "INDEPENDENT-TEST",
    "INDEPENDENT-REVIEW",
    "EVIDENCE-VERIFICATION",
    "TECHNICAL-ACCEPTANCE",
    "OWNER-ACCEPTANCE",
    "RELEASE-AUTHORIZATION",
    "PRODUCTION-OBSERVATION",
}
EVIDENCE_LEVELS = {"E0", "E1", "E2", "E3", "E4"}
EVIDENCE_ORDER = {level: position for position, level in enumerate(("E0", "E1", "E2", "E3", "E4"))}
IDENTITY_CAPABILITIES = {"none", "session-label", "host-principal", "cryptographically-attested"}
CAPABILITY_VALUES = {
    "skill_routing": {"explicit-only", "implicit-best-effort", "session-bootstrap"},
    "tool_mediation": {"none", "advisory", "wrapper", "sandbox-policy"},
    "agent_identity": IDENTITY_CAPABILITIES,
    "workspace_isolation": {"none", "branch", "worktree", "sandbox"},
    "test_evidence": {"agent-reported", "reproducible", "host-observed", "ci-attested"},
    "browser_verification": {"unavailable", "manual", "host-automated"},
    "ci_cd_integration": {"unavailable", "reporting-only", "protected-artifact", "protected-deploy"},
    "secret_boundary": {"prompt-exposed", "environment-scoped", "short-lived-protected"},
    "production_control": {"none", "owner-confirmed", "ci-protected"},
}
ID_RE = re.compile(r"^[a-z][a-z0-9-]{2,63}$")
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
GIT_REVISION_RE = re.compile(r"^[0-9a-f]{40}$")
TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$")


def canonical_relative_path(value: object) -> bool:
    """Return whether value is a portable, traversal-free relative POSIX path."""
    if not isinstance(value, str) or not value.strip() or "\\" in value:
        return False
    candidate = PurePosixPath(value)
    return not candidate.is_absolute() and bool(candidate.parts) and all(
        part not in {"", ".", ".."} for part in candidate.parts
    )


def parse_utc(value: object) -> datetime | None:
    if not isinstance(value, str) or not TIMESTAMP_RE.fullmatch(value):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _non_empty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _non_empty_strings(value: object) -> bool:
    return isinstance(value, list) and bool(value) and all(_non_empty_string(item) for item in value)


def _validate_capabilities(profile: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(profile, dict):
        return ["capability_profile must be an object"]
    for field, allowed in CAPABILITY_VALUES.items():
        value = profile.get(field)
        if value not in allowed:
            errors.append(f"capability_profile.{field} must be one of: {', '.join(sorted(allowed))}")
    return errors


def _validate_sources(sources: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(sources, list) or not sources:
        return ["approved_sources must be a non-empty list"]
    identifiers: set[str] = set()
    for index, source in enumerate(sources, start=1):
        label = f"approved_sources[{index}]"
        if not isinstance(source, dict):
            errors.append(f"{label} must be an object")
            continue
        identifier = source.get("id")
        if not isinstance(identifier, str) or not ID_RE.fullmatch(identifier):
            errors.append(f"{label}.id must be a lowercase hyphenated identifier")
        elif identifier in identifiers:
            errors.append(f"{label}.id is duplicated")
        else:
            identifiers.add(identifier)
        if not canonical_relative_path(source.get("path")):
            errors.append(f"{label}.path must be a canonical relative path")
        if not isinstance(source.get("sha256"), str) or not SHA256_RE.fullmatch(source["sha256"]):
            errors.append(f"{label}.sha256 must be a sha256 fingerprint")
    return errors


def _validate_scope(scope: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(scope, dict):
        return ["scope must be an object"]
    owned_targets = scope.get("owned_targets")
    if not isinstance(owned_targets, list) or not owned_targets:
        errors.append("scope.owned_targets must be a non-empty list")
    elif not all(canonical_relative_path(path) for path in owned_targets):
        errors.append("scope.owned_targets must use canonical relative paths")
    elif len(set(owned_targets)) != len(owned_targets):
        errors.append("scope.owned_targets must not contain duplicates")
    for field in ("interfaces", "database_objects", "environments", "parallel_write_groups"):
        if not isinstance(scope.get(field), list):
            errors.append(f"scope.{field} must be a list")
    return errors


def _validate_authority(authority: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(authority, dict):
        return ["authority must be an object"]
    if not isinstance(authority.get("mutation_allowed"), bool):
        errors.append("authority.mutation_allowed must be boolean")
    if authority.get("dependency_changes") not in {"forbidden", "approved-only"}:
        errors.append("authority.dependency_changes must be forbidden or approved-only")
    if authority.get("production_action") not in {"prohibited", "owner-authorized", "ci-protected"}:
        errors.append("authority.production_action must be prohibited, owner-authorized, or ci-protected")
    commands = authority.get("allowed_commands")
    if not isinstance(commands, list):
        errors.append("authority.allowed_commands must be a list")
        return errors
    command_ids: set[str] = set()
    for index, command in enumerate(commands, start=1):
        label = f"authority.allowed_commands[{index}]"
        if not isinstance(command, dict):
            errors.append(f"{label} must be an object")
            continue
        identifier = command.get("id")
        if not isinstance(identifier, str) or not ID_RE.fullmatch(identifier):
            errors.append(f"{label}.id must be a lowercase hyphenated identifier")
        elif identifier in command_ids:
            errors.append(f"{label}.id is duplicated")
        else:
            command_ids.add(identifier)
        argv = command.get("argv")
        if not _non_empty_strings(argv):
            errors.append(f"{label}.argv must be a non-empty string list")
        if command.get("cwd") != "." and not canonical_relative_path(command.get("cwd")):
            errors.append(f"{label}.cwd must be . or a canonical relative path")
        timeout = command.get("timeout_seconds")
        if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout <= 0 or timeout > 3600:
            errors.append(f"{label}.timeout_seconds must be an integer from 1 to 3600")
    return errors


def _validate_roles(roles: object, capability_profile: object, evidence_level: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(roles, dict):
        return ["roles must be an object"]
    identities = [roles.get(field) for field in ("implementer_id", "tester_id", "reviewer_id")]
    if not all(_non_empty_string(identity) for identity in identities):
        errors.append("roles requires implementer_id, tester_id, and reviewer_id")
    elif len(set(identities)) != 3:
        errors.append("roles implementer_id, tester_id, and reviewer_id must be distinct declared identities")
    claim = roles.get("independence_claim")
    if claim not in {"not-attested", "host-attested"}:
        errors.append("roles.independence_claim must be not-attested or host-attested")
    elif claim == "host-attested":
        identity = capability_profile.get("agent_identity") if isinstance(capability_profile, dict) else None
        if identity not in {"host-principal", "cryptographically-attested"}:
            errors.append("host-attested independence requires host-principal or cryptographically-attested identity")
        if evidence_level not in {"E3", "E4"}:
            errors.append("host-attested independence requires E3 or E4 evidence")
    return errors


def validate_contract(data: object, *, now: datetime | None = None) -> list[str]:
    """Return schema, authority, freshness, and assurance blockers for a v2 contract."""
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["contract must be a JSON object"]
    if data.get("schema_version") != CONTRACT_SCHEMA_VERSION:
        errors.append(f"schema_version must be {CONTRACT_SCHEMA_VERSION}")
    if not isinstance(data.get("contract_id"), str) or not ID_RE.fullmatch(data["contract_id"]):
        errors.append("contract_id must be a lowercase hyphenated identifier")
    if data.get("status") not in {"proposed", "active", "paused", "closed", "cancelled"}:
        errors.append("status must be proposed, active, paused, closed, or cancelled")

    project = data.get("project")
    if not isinstance(project, dict):
        errors.append("project must be an object")
    else:
        if not _non_empty_string(project.get("id")):
            errors.append("project.id is required")
        if not isinstance(project.get("baseline_revision"), str) or not GIT_REVISION_RE.fullmatch(project["baseline_revision"]):
            errors.append("project.baseline_revision must be a 40-character Git revision")

    if data.get("lifecycle_state") not in LIFECYCLE_STATES:
        errors.append("lifecycle_state must be a recognized governed lifecycle state")
    risk = data.get("risk_track")
    if risk not in RISK_TRACKS:
        errors.append("risk_track must be Fast, Standard, Enhanced, or Critical")

    created_at = parse_utc(data.get("created_at"))
    expires_at = parse_utc(data.get("expires_at"))
    if created_at is None:
        errors.append("created_at must be a UTC timestamp")
    if expires_at is None:
        errors.append("expires_at must be a UTC timestamp")
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        errors.append("now must be timezone-aware")
    if created_at and expires_at and expires_at <= created_at:
        errors.append("expires_at must be after created_at")
    if expires_at and now.tzinfo and expires_at < now:
        errors.append("contract is expired and cannot authorize work")

    outcome = data.get("outcome")
    if not isinstance(outcome, dict):
        errors.append("outcome must be an object")
    else:
        if not _non_empty_string(outcome.get("owner_visible_result")):
            errors.append("outcome.owner_visible_result is required")
        for field in ("acceptance_criteria", "exclusions", "non_goals", "success_metrics"):
            if not _non_empty_strings(outcome.get(field)):
                errors.append(f"outcome.{field} must be a non-empty string list")

    errors.extend(_validate_sources(data.get("approved_sources")))
    errors.extend(_validate_scope(data.get("scope")))
    errors.extend(_validate_authority(data.get("authority")))

    evidence = data.get("evidence")
    evidence_level: object = None
    if not isinstance(evidence, dict):
        errors.append("evidence must be an object")
    else:
        evidence_level = evidence.get("minimum_level")
        if evidence_level not in EVIDENCE_LEVELS:
            errors.append("evidence.minimum_level must be E0, E1, E2, E3, or E4")
        freshness = evidence.get("freshness_hours")
        if not isinstance(freshness, int) or isinstance(freshness, bool) or freshness <= 0 or freshness > 720:
            errors.append("evidence.freshness_hours must be an integer from 1 to 720")
        if not _non_empty_strings(evidence.get("required_checks")):
            errors.append("evidence.required_checks must be a non-empty string list")
        if risk in {"Enhanced", "Critical"} and evidence_level in EVIDENCE_ORDER and EVIDENCE_ORDER[evidence_level] < EVIDENCE_ORDER["E2"]:
            errors.append(f"{risk} work requires E2 or stronger evidence; self-written evidence cannot be Verified")

    capability_profile = data.get("capability_profile")
    errors.extend(_validate_capabilities(capability_profile))
    errors.extend(_validate_roles(data.get("roles"), capability_profile, evidence_level))

    operations = data.get("operations")
    if not isinstance(operations, dict):
        errors.append("operations must be an object")
    else:
        for field in ("rollback_or_forward_recovery", "observation_period"):
            if not _non_empty_string(operations.get(field)):
                errors.append(f"operations.{field} is required")
        if not _non_empty_strings(operations.get("stop_conditions")):
            errors.append("operations.stop_conditions must be a non-empty string list")

    economics = data.get("economics")
    if not isinstance(economics, dict):
        errors.append("economics must be an object")
    else:
        for field in ("model_tier", "reasoning_effort", "max_cost"):
            if not _non_empty_string(economics.get(field)):
                errors.append(f"economics.{field} is required")
        for field in ("max_turns", "fix_circuit_breaker"):
            value = economics.get(field)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                errors.append(f"economics.{field} must be a non-negative integer")

    return list(dict.fromkeys(errors))


def load_contract(path: Path, *, now: datetime | None = None) -> dict:
    """Load one regular JSON contract and raise ValueError when it is unsafe or invalid."""
    supplied = Path(path)
    try:
        mode = supplied.lstat().st_mode
        resolved = supplied.resolve(strict=True)
    except OSError as exc:
        raise ValueError(f"cannot resolve contract: {exc}") from exc
    if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
        raise ValueError("contract must be a regular file")
    try:
        data = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read contract JSON: {exc}") from exc
    errors = validate_contract(data, now=now)
    if errors:
        raise ValueError("invalid contract: " + "; ".join(errors))
    return data
