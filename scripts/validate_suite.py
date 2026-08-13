#!/usr/bin/env python3
"""Validate the portable Governed Multi-Agent Skill Suite."""

from __future__ import annotations

import hashlib
import importlib.util
import os
import re
import secrets
import stat
import sys
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath
from urllib.parse import unquote


EXPECTED_SKILLS = {
    "architect-system-deliberately",
    "assure-quality-systematically",
    "debug-from-root-cause",
    "design-human-centered-experience",
    "develop-test-first",
    "engineer-backend-and-data",
    "engineer-frontend-accessibly",
    "engineer-performance-and-reliability",
    "execute-approved-work",
    "guard-approved-artifacts",
    "init-owner-governance",
    "orchestrate-owner-governed-delivery",
    "plan-governed-implementation",
    "prepare-safe-workspace",
    "review-governed-change",
    "secure-and-protect-system",
    "shape-feature-foundation",
    "specify-approved-change",
    "verify-implementation",
    "verify-production-release",
    "using-governed-suite",
    "coordinate-isolated-agent-execution",
    "govern-data-change-safely",
    "evaluate-governed-agent-behavior",
}

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
RESOURCE_RE = re.compile(r"(?:`|\]\()((?:assets|references|scripts)/[^`\s)]+)")
MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
OFFICIAL_SKILLS_DOC_URL = "https://learn.chatgpt.com/docs/build-skills"
FORBIDDEN_RUNTIME_PATHS = ("/root/.codex", "/root/")
RELEASE_DOCUMENTS = (
    "README.md",
    "INSTALL.md",
    "LICENSE",
    "NOTICE",
    "SECURITY.md",
    "SHA256SUMS",
    "docs/EXPORT_MANIFEST.md",
    "docs/FEATURE_FOUNDATION_v1.2.md",
    "docs/HARDENING_v1.2.1.md",
    "docs/RELEASE_INTEGRITY.md",
    "docs/RELEASE_NOTES_v1.2.2.md",
    "docs/RELEASE_NOTES_v1.2.3.md",
    "docs/RELEASE_NOTES_v2.0.0-rc.1.md",
    "docs/v2/OWNER_PROTECTION_FOUNDATION.md",
    "docs/v2/CAPABILITY_MATRIX.md",
    "docs/v2/UPGRADE_PATH.md",
    "evaluations/README.md",
    "evaluations/adversarial-scenarios.json",
    "scripts/validate_evaluation_suite.py",
)
WORKFLOW = ".github/workflows/validate.yml"
ACTION_USE_RE = re.compile(r"(?m)^\s*-\s*uses:\s*([A-Za-z0-9_.\-/]+)@([^\s#]+)")
FULL_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
EXPECTED_ACTION_PINS = {
    "actions/checkout": "11d5960a326750d5838078e36cf38b85af677262",
    "actions/setup-python": "a26af69be951a213d495a4c3e4e4022e16d87065",
}
DIRECT_INVOCATION_PHRASES = (
    "## Direct invocation boundary",
    "assignment contract",
    "read-only consultation",
    "do not modify a project",
)
ROUTER_SKILLS = {"orchestrate-owner-governed-delivery", "using-governed-suite"}
V2_EXISTING_SKILLS = EXPECTED_SKILLS - {
    "using-governed-suite",
    "coordinate-isolated-agent-execution",
    "govern-data-change-safely",
    "evaluate-governed-agent-behavior",
}
V2_COMMON_CONTROL_PHRASES = (
    "## V2 contract and evidence boundary",
    "$using-governed-suite",
    "Verified",
    "Reproducible",
    "Reported",
    "Inferred",
    "Unknown",
    "Failed",
)
V2_REQUIRED_PATHS = (
    "adapters/local-evidence-runner/run_governed_command.py",
    "adapters/local-evidence-runner/verify_receipt.py",
    "adapters/local-evidence-runner/README.md",
    "skills/using-governed-suite/scripts/contract_rules.py",
    "skills/using-governed-suite/scripts/validate_work_package_contract.py",
    "skills/coordinate-isolated-agent-execution/scripts/prepare_isolated_workspace.py",
    "skills/coordinate-isolated-agent-execution/scripts/validate_execution_ledger.py",
    "skills/govern-data-change-safely/scripts/validate_data_change_plan.py",
    "skills/evaluate-governed-agent-behavior/scripts/validate_evaluation_run.py",
    "skills/evaluate-governed-agent-behavior/scripts/generate_scorecard.py",
    ".github/workflows/validate.yml",
)
CHECKSUM_FILE = "SHA256SUMS"
CHECKSUM_LINE_RE = re.compile(r"^([0-9a-f]{64})  ([^\s].*)$")
CHECKSUM_EXCLUDED_PARTS = {".git", "__pycache__"}
OPENAI_INTERFACE_FIELDS = {
    "display_name",
    "short_description",
    "default_prompt",
    "icon_small",
    "icon_large",
}
OPENAI_POLICY_FIELDS = {"allow_implicit_invocation", "products"}
OPENAI_PRODUCTS = {"CHAT", "CODEX"}
SVG_DIMENSION_RE = re.compile(r"^\s*([1-9][0-9]*(?:\.[0-9]+)?)\s*(?:px)?\s*$")
MINIMUM_PLUGIN_ICON_DIMENSION = 48


def validate_openai_yaml(ui_file: Path, skill_name: str) -> list[str]:
    """Validate the suite's documented OpenAI metadata subset without a YAML dependency."""
    errors: list[str] = []
    try:
        lines = ui_file.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        return [f"agents/openai.yaml cannot be read: {exc}"]

    section: str | None = None
    policy_list: str | None = None
    seen_top: set[str] = set()
    interface_values: dict[str, str] = {}
    policy_values: dict[str, object] = {}

    for number, raw_line in enumerate(lines, start=1):
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if "\t" in raw_line:
            errors.append(f"agents/openai.yaml invalid YAML at line {number}: tabs are not supported")
            continue
        indentation = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()

        if indentation == 0:
            match = re.fullmatch(r"(interface|policy):", line)
            if not match:
                errors.append(f"agents/openai.yaml invalid YAML at line {number}: expected top-level mapping key")
                section = None
                continue
            section = match.group(1)
            if section in seen_top:
                errors.append(f"agents/openai.yaml invalid YAML at line {number}: duplicate top-level key {section}")
            seen_top.add(section)
            policy_list = None
            continue

        if indentation == 2 and section == "interface":
            match = re.fullmatch(r"([a-z_]+):\s*(.+)", line)
            if not match:
                errors.append(f"agents/openai.yaml invalid YAML at line {number}: expected an interface scalar")
                continue
            field, value = match.groups()
            if field not in OPENAI_INTERFACE_FIELDS:
                errors.append(f"agents/openai.yaml invalid YAML at line {number}: unsupported interface field {field}")
                continue
            if field in interface_values:
                errors.append(f"agents/openai.yaml invalid YAML at line {number}: duplicate interface field {field}")
                continue
            if value.startswith(("[", "{", "|", ">")):
                errors.append(f"agents/openai.yaml invalid YAML at line {number}: unsupported interface scalar")
                continue
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
                value = value[1:-1]
            interface_values[field] = value
            continue

        if indentation == 4 and section == "policy" and policy_list == "products":
            if not line.startswith("- "):
                errors.append(f"agents/openai.yaml invalid YAML at line {number}: expected a products list item")
                continue
            product = line[2:].strip()
            if product not in OPENAI_PRODUCTS:
                errors.append(f"agents/openai.yaml invalid YAML at line {number}: unsupported product {product}")
                continue
            policy_values.setdefault("products", []).append(product)
            continue

        if indentation == 2 and section == "policy":
            match = re.fullmatch(r"([a-z_]+):\s*(.*)", line)
            if not match:
                errors.append(f"agents/openai.yaml invalid YAML at line {number}: expected a policy key")
                continue
            field, value = match.groups()
            if field not in OPENAI_POLICY_FIELDS:
                errors.append(f"agents/openai.yaml invalid YAML at line {number}: unsupported policy field {field}")
                continue
            if field in policy_values:
                errors.append(f"agents/openai.yaml invalid YAML at line {number}: duplicate policy field {field}")
                continue
            if field == "allow_implicit_invocation":
                if value not in {"true", "false"}:
                    errors.append(f"agents/openai.yaml invalid YAML at line {number}: allow_implicit_invocation must be true or false")
                    continue
                policy_values[field] = value == "true"
                policy_list = None
            else:
                if value:
                    errors.append(f"agents/openai.yaml invalid YAML at line {number}: products must be a list")
                    continue
                policy_values[field] = []
                policy_list = field
            continue

        errors.append(f"agents/openai.yaml invalid YAML at line {number}: unsupported indentation or structure")

    missing_interface = OPENAI_INTERFACE_FIELDS - set(interface_values)
    if missing_interface:
        errors.append("agents/openai.yaml invalid YAML: missing interface fields: " + ", ".join(sorted(missing_interface)))
    if set(policy_values) != OPENAI_POLICY_FIELDS:
        missing_policy = OPENAI_POLICY_FIELDS - set(policy_values)
        if missing_policy:
            errors.append("agents/openai.yaml invalid YAML: missing policy fields: " + ", ".join(sorted(missing_policy)))
    products = policy_values.get("products")
    if isinstance(products, list) and (
        not products or not set(products).issubset(OPENAI_PRODUCTS) or len(products) != len(set(products))
    ):
        errors.append("agents/openai.yaml invalid YAML: products must list CHAT, CODEX, or both without duplicates")
    if interface_values.get("default_prompt", "").find(f"${skill_name}") == -1:
        errors.append("agents/openai.yaml default_prompt must mention the skill name")
    skill_root = ui_file.parents[1]
    validated_assets: set[Path] = set()
    for field in ("icon_small", "icon_large"):
        value = interface_values.get(field, "")
        if not value.startswith("./"):
            errors.append(f"agents/openai.yaml {field} must start with ./")
            continue
        asset = skill_root / value[2:]
        try:
            resolved_asset = asset.resolve(strict=True)
            resolved_asset.relative_to(skill_root.resolve(strict=True))
        except (OSError, ValueError):
            errors.append(f"agents/openai.yaml {field} must reference a contained asset")
            continue
        if asset.is_symlink() or not resolved_asset.is_file():
            errors.append(f"agents/openai.yaml {field} must reference a regular file")
            continue
        if resolved_asset in validated_assets:
            continue
        validated_assets.add(resolved_asset)
        if resolved_asset.suffix.lower() != ".svg":
            continue
        try:
            root = ET.fromstring(resolved_asset.read_text(encoding="utf-8"))
        except (ET.ParseError, OSError, UnicodeError) as exc:
            errors.append(f"agents/openai.yaml {field} SVG cannot be parsed: {exc}")
            continue
        dimensions: list[float] = []
        for dimension in ("width", "height"):
            value = root.get(dimension, "")
            match = SVG_DIMENSION_RE.fullmatch(value)
            if not match:
                errors.append(f"agents/openai.yaml {field} SVG must declare a numeric {dimension}")
                break
            dimensions.append(float(match.group(1)))
        else:
            width, height = dimensions
            if width != height or width < MINIMUM_PLUGIN_ICON_DIMENSION:
                errors.append(
                    f"agents/openai.yaml {field} SVG must be square and at least "
                    f"{MINIMUM_PLUGIN_ICON_DIMENSION} by {MINIMUM_PLUGIN_ICON_DIMENSION}"
                )
    return errors


def validate_release_documents(repo: Path) -> list[str]:
    """Check release documents, local Markdown links, and installation safety claims."""
    errors: list[str] = []
    documents = {name: repo / name for name in RELEASE_DOCUMENTS}
    for name, document in documents.items():
        if not document.is_file():
            errors.append(f"missing {name}")

    if errors:
        return errors

    resolved_repo = repo.resolve()
    for name, document in documents.items():
        if not document.is_file():
            continue
        text = document.read_text(encoding="utf-8")
        for forbidden_path in FORBIDDEN_RUNTIME_PATHS:
            if forbidden_path in text:
                errors.append(f"{name} exposes an internal runtime path: {forbidden_path}")
        for raw_destination in MARKDOWN_LINK_RE.findall(text):
            destination = raw_destination.strip().split(maxsplit=1)[0]
            if not destination or destination.startswith("#") or re.match(
                r"[a-z][a-z0-9+.-]*:", destination, flags=re.IGNORECASE
            ):
                continue
            local_path = destination.split("#", 1)[0].split("?", 1)[0]
            target = (document.parent / unquote(local_path)).resolve()
            try:
                target.relative_to(resolved_repo)
            except ValueError:
                errors.append(f"{name} has local Markdown link outside the release: {destination}")
            else:
                if not target.exists():
                    errors.append(f"{name} has broken local Markdown link: {destination}")

    if not all(documents[name].is_file() for name in ("README.md", "INSTALL.md", "docs/EXPORT_MANIFEST.md")):
        return errors

    readme = documents["README.md"].read_text(encoding="utf-8")
    guide = documents["INSTALL.md"].read_text(encoding="utf-8")
    manifest = documents["docs/EXPORT_MANIFEST.md"].read_text(encoding="utf-8")
    release_integrity = documents["docs/RELEASE_INTEGRITY.md"].read_text(encoding="utf-8")
    time_sensitive_publication_claims = (
        "not yet published as a GitHub release",
        "not a public release",
        "this source has not yet been published",
    )
    for name, text in (("README.md", readme), ("docs/EXPORT_MANIFEST.md", manifest)):
        if any(claim.lower() in text.lower() for claim in time_sensitive_publication_claims):
            errors.append(f"{name} contains a time-sensitive publication claim")
    if "Install only from a published versioned tag or release archive, not from a mutable branch." not in readme:
        errors.append("README.md must direct users to a published versioned tag or release archive")
    if "](INSTALL.md)" not in readme:
        errors.append("README.md must link directly to INSTALL.md")
    if (
        "ChatGPT Work on the web" not in readme
        or "not a plugin" not in readme.lower()
        or "host-level access control" not in readme
    ):
        errors.append("README.md must distinguish local standalone skills from ChatGPT Work on the web plugins")
    if "](../INSTALL.md)" not in manifest:
        errors.append("docs/EXPORT_MANIFEST.md must link directly to INSTALL.md")
    if any(
        concept not in guide
        for concept in (
            "technical user",
            "$HOME/.agents/skills",
            ".agents/skills",
            "POSIX-compatible",
            "scripts/install_repo_skills.py",
            "--verify-installed",
        )
    ):
        errors.append("INSTALL.md is missing a supported, checked local installation route")
    if "do not overwrite" not in guide.lower() or "collision" not in guide.lower():
        errors.append("INSTALL.md must state the no-overwrite collision safeguard")
    route_a = re.search(r"^## Supported route.*?(?=^## |\Z)", guide, flags=re.DOTALL | re.MULTILINE)
    if (
        not route_a
        or "--suite-dir" not in route_a.group(0)
        or "--project-root" not in route_a.group(0)
        or "does not merge, overwrite" not in route_a.group(0)
        or "temporary directory" not in route_a.group(0)
    ):
        errors.append("INSTALL.md must provide one exact, no-overwrite repository installation command")
    installer = repo / "scripts" / "install_repo_skills.py"
    if not installer.is_file():
        errors.append("missing scripts/install_repo_skills.py")
    web_claim = re.compile(
        r"(?ism)^## What installation route is correct\?.*?ChatGPT Work on the web.*?separately packaged and permitted plugin"
    )
    if not web_claim.search(guide):
        errors.append(
            "INSTALL.md must state that ChatGPT Work on the web cannot install these raw folders and requires a permitted plugin"
        )
    if (
        OFFICIAL_SKILLS_DOC_URL not in guide
        or any(term not in guide.lower() for term in ("plan", "platform", "administrator"))
    ):
        errors.append(
            "INSTALL.md must link to the official skills documentation and explain plan, platform, and administrator controls"
        )
    if "before creating the tag" not in release_integrity:
        errors.append("docs/RELEASE_INTEGRITY.md must seal SHA256SUMS before creating the release tag")
    if (
        "Never use `--write` when checking a downloaded or copied release" not in release_integrity
        or "--release-maintainer" not in release_integrity
    ):
        errors.append("docs/RELEASE_INTEGRITY.md must separate consumer verification from maintainer inventory generation")
    foundation = documents["docs/FEATURE_FOUNDATION_v1.2.md"].read_text(encoding="utf-8")
    if "Historical design reference" not in foundation or "No completed approval record is included" not in foundation:
        errors.append("Feature Foundation must not present a blank approval template as a completed approval record")
    if "approved v1.2 Feature Foundation" in manifest:
        errors.append("Export manifest must not claim that the bundled Feature Foundation is approved")
    notes = documents["docs/RELEASE_NOTES_v1.2.2.md"].read_text(encoding="utf-8")
    if "not yet a published GitHub release" not in notes or "does not prove a live Codex host" not in notes:
        errors.append("v1.2.2 release notes must state the publication and live-discovery limits")
    current_notes = documents["docs/RELEASE_NOTES_v1.2.3.md"].read_text(encoding="utf-8")
    if (
        "does not assert publication status" not in current_notes
        or "does not prove a live Codex host" not in current_notes
    ):
        errors.append("v1.2.3 release notes must state the publication and live-discovery limits")
    v2_notes = documents["docs/RELEASE_NOTES_v2.0.0-rc.1.md"].read_text(encoding="utf-8")
    v2_foundation = documents["docs/v2/OWNER_PROTECTION_FOUNDATION.md"].read_text(encoding="utf-8")
    capability_matrix = documents["docs/v2/CAPABILITY_MATRIX.md"].read_text(encoding="utf-8")
    upgrade_path = documents["docs/v2/UPGRADE_PATH.md"].read_text(encoding="utf-8")
    if "not behaviorally evaluated" not in v2_notes.lower() or "release candidate" not in v2_notes.lower():
        errors.append("v2 release notes must identify the source as an unevaluated release candidate")
    if "Owner Truth Card" not in v2_foundation or "trusted host" not in v2_foundation:
        errors.append("v2 foundation must state the owner card and trusted-host boundary")
    if "explicit-only" not in capability_matrix or "not enforcement" not in capability_matrix.lower():
        errors.append("v2 capability matrix must describe explicit routing and non-enforcement honestly")
    if "v1.2.3" not in upgrade_path or "no overwrite" not in upgrade_path.lower():
        errors.append("v2 upgrade path must explain safe migration from v1.2.3 without overwrite")
    if (
        "Version 2.0.0-rc.1" not in readme
        or "24 focused Codex skills" not in readme
        or "$using-governed-suite" not in readme
        or "not behaviorally evaluated" not in readme.lower()
    ):
        errors.append("README.md must identify the 24-skill v2 release candidate and first-turn router honestly")
    if (
        "24 standalone skill folders" not in guide
        or "all 24 skills" not in guide
        or "$using-governed-suite Explain the owner-governed workflow" not in guide
    ):
        errors.append("INSTALL.md must describe 24-skill v2 discovery through the first-turn router")
    if (
        "Version: 2.0.0-rc.1" not in manifest
        or "24 portable skills" not in manifest
        or "Eighteen adversarial evaluation fixtures" not in manifest
        or "release candidate" not in manifest.lower()
    ):
        errors.append("Export manifest must describe the v2 release-candidate scope without a behavior claim")
    security = documents["SECURITY.md"].read_text(encoding="utf-8")
    if (
        "v2.0.0-rc.1 standalone validator commands" not in security
        or "E1 reproducible receipt" not in security
        or "Neither mode proves independent agent identity" not in security
    ):
        errors.append("SECURITY.md must state the local runner assurance boundary accurately")
    return errors


def validate_specialist_invocation_boundaries(repo: Path) -> list[str]:
    """Require every specialist to refuse project mutation without orchestration."""
    errors: list[str] = []
    for skill_name in sorted(EXPECTED_SKILLS - ROUTER_SKILLS):
        skill_file = repo / "skills" / skill_name / "SKILL.md"
        ui_file = repo / "skills" / skill_name / "agents" / "openai.yaml"
        if not skill_file.is_file():
            continue
        text = skill_file.read_text(encoding="utf-8")
        if any(phrase not in text for phrase in DIRECT_INVOCATION_PHRASES):
            errors.append(f"{skill_name} lacks the required direct-invocation safety boundary")
        if not ui_file.is_file() or "allow_implicit_invocation: false" not in ui_file.read_text(encoding="utf-8"):
            errors.append(f"{skill_name} must disable implicit invocation")
    return errors


def validate_v2_owner_protection_spine(repo: Path) -> list[str]:
    """Require v2 controls while preserving the line between procedures and enforcement."""
    errors: list[str] = []
    for relative in V2_REQUIRED_PATHS:
        path = repo / relative
        if not path.is_file():
            errors.append(f"missing v2 owner-protection resource: {relative}")
    for skill_name in sorted(V2_EXISTING_SKILLS):
        skill_file = repo / "skills" / skill_name / "SKILL.md"
        if not skill_file.is_file():
            continue
        text = skill_file.read_text(encoding="utf-8")
        missing = [phrase for phrase in V2_COMMON_CONTROL_PHRASES if phrase not in text]
        if missing:
            errors.append(f"{skill_name} lacks common v2 controls: {', '.join(missing)}")
    router = repo / "skills" / "using-governed-suite" / "SKILL.md"
    if router.is_file():
        text = router.read_text(encoding="utf-8")
        for phrase in ("Orientation Card", "Owner Truth Card", "not a claim that the host automatically enforces governance"):
            if phrase not in text:
                errors.append(f"using-governed-suite lacks required routing boundary: {phrase}")
    return errors


def validate_workflow_security(repo: Path) -> list[str]:
    """Reject mutable CI action references and avoid needless credentials."""
    workflow = repo / WORKFLOW
    if not workflow.is_file():
        return [f"missing {WORKFLOW}"]
    text = workflow.read_text(encoding="utf-8")
    errors: list[str] = []
    actions = ACTION_USE_RE.findall(text)
    if not actions:
        errors.append(f"{WORKFLOW} has no parsed action references")
    for action, ref in actions:
        if not FULL_SHA_RE.fullmatch(ref):
            errors.append(f"{WORKFLOW} action {action}@{ref} is not pinned to an immutable full SHA")
        elif action in EXPECTED_ACTION_PINS and ref != EXPECTED_ACTION_PINS[action]:
            errors.append(f"{WORKFLOW} action {action} does not use the reviewed immutable pin")
    if not re.search(r"(?m)^\s*contents:\s*read\s*$", text):
        errors.append(f"{WORKFLOW} must declare contents: read and no broader default permission")
    if re.search(r"(?m)^\s*[a-z-]+:\s*write\s*$", text):
        errors.append(f"{WORKFLOW} must not grant a write permission")
    if "persist-credentials: false" not in text:
        errors.append(f"{WORKFLOW} must disable persisted checkout credentials")
    if "runs-on: ubuntu-latest" in text:
        errors.append(f"{WORKFLOW} must not use the mutable ubuntu-latest label")
    if 'python-version: "3.12"' not in text:
        errors.append(f"{WORKFLOW} must pin the Python minor version used for validation")
    required_commands = (
        "python scripts/validate_suite.py",
        "python scripts/release_checksums.py",
        "python scripts/validate_evaluation_suite.py",
        "python -m unittest discover -s tests -p 'test_*.py' -v",
        "python -m compileall -q scripts skills",
    )
    for command in required_commands:
        if command not in text:
            errors.append(f"{WORKFLOW} must run {command!r}")
    if "timeout-minutes:" not in text:
        errors.append(f"{WORKFLOW} must define a job timeout")
    return errors


def _release_root(repo: Path) -> Path:
    try:
        root = Path(repo).resolve(strict=True)
    except OSError as exc:
        raise ValueError(f"cannot resolve release root: {exc}") from exc
    if not root.is_dir():
        raise ValueError("release root is not a directory")
    return root


def _release_open_flags(*, directory: bool) -> int:
    if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
        raise ValueError("safe release validation requires POSIX O_NOFOLLOW, O_DIRECTORY, and dir_fd support")
    flags = os.O_RDONLY | os.O_NOFOLLOW
    if directory:
        flags |= os.O_DIRECTORY
    elif hasattr(os, "O_NONBLOCK"):
        flags |= os.O_NONBLOCK
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    return flags


def _release_relative_parts(value: str) -> tuple[str, tuple[str, ...]]:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("release path must be a non-empty forward-slash path")
    pure = PurePosixPath(value)
    if pure.is_absolute() or not pure.parts or any(part in {"", ".", ".."} for part in pure.parts):
        raise ValueError("release path must be canonical and relative")
    return pure.as_posix(), pure.parts


def open_contained_release_file(repo: Path, value: str) -> tuple[int, str]:
    """Open one regular release file through descriptor-bound traversal."""
    root = _release_root(repo)
    relative, parts = _release_relative_parts(value)
    directory_descriptor = -1
    file_descriptor = -1
    try:
        directory_descriptor = os.open(root, _release_open_flags(directory=True))
        for part in parts[:-1]:
            next_descriptor = os.open(part, _release_open_flags(directory=True), dir_fd=directory_descriptor)
            os.close(directory_descriptor)
            directory_descriptor = next_descriptor
        file_descriptor = os.open(parts[-1], _release_open_flags(directory=False), dir_fd=directory_descriptor)
        if not stat.S_ISREG(os.fstat(file_descriptor).st_mode):
            raise ValueError(f"release path is not a regular file: {relative}")
        descriptor, file_descriptor = file_descriptor, -1
        return descriptor, relative
    except ValueError:
        raise
    except (OSError, TypeError) as exc:
        raise ValueError(f"cannot open release path safely: {relative}") from exc
    finally:
        if file_descriptor != -1:
            os.close(file_descriptor)
        if directory_descriptor != -1:
            os.close(directory_descriptor)


def read_contained_release_file(repo: Path, value: str) -> tuple[bytes, str]:
    """Read one regular release file without reopening its path by name."""
    descriptor, relative = open_contained_release_file(repo, value)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError(f"release path is not a regular file: {relative}")
        chunks: list[bytes] = []
        while chunk := os.read(descriptor, 65536):
            chunks.append(chunk)
        after = os.fstat(descriptor)
        if (
            (before.st_dev, before.st_ino, stat.S_IFMT(before.st_mode))
            != (after.st_dev, after.st_ino, stat.S_IFMT(after.st_mode))
            or before.st_size != after.st_size
            or before.st_mtime_ns != after.st_mtime_ns
        ):
            raise ValueError(f"release path changed while being read: {relative}")
        return b"".join(chunks), relative
    except OSError as exc:
        raise ValueError(f"cannot read release path safely: {relative}") from exc
    finally:
        os.close(descriptor)


def sha256_contained_release_file(repo: Path, value: str) -> tuple[str, str]:
    descriptor, relative = open_contained_release_file(repo, value)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError(f"release path is not a regular file: {relative}")
        digest = hashlib.sha256()
        while chunk := os.read(descriptor, 65536):
            digest.update(chunk)
        after = os.fstat(descriptor)
        if (
            (before.st_dev, before.st_ino, stat.S_IFMT(before.st_mode))
            != (after.st_dev, after.st_ino, stat.S_IFMT(after.st_mode))
            or before.st_size != after.st_size
            or before.st_mtime_ns != after.st_mtime_ns
        ):
            raise ValueError(f"release path changed while being hashed: {relative}")
        return digest.hexdigest(), relative
    except OSError as exc:
        raise ValueError(f"cannot hash release path safely: {relative}") from exc
    finally:
        os.close(descriptor)


def release_hashes(repo: Path) -> tuple[dict[str, str], list[str]]:
    """Return hashes for every distributable regular file, excluding SHA256SUMS itself."""
    hashes: dict[str, str] = {}
    errors: list[str] = []
    try:
        root = _release_root(repo)
    except ValueError as exc:
        return hashes, [str(exc)]
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if relative == CHECKSUM_FILE or any(part in CHECKSUM_EXCLUDED_PARTS for part in path.relative_to(root).parts):
            continue
        try:
            mode = path.lstat().st_mode
        except OSError as exc:
            errors.append(f"cannot inspect release path: {relative}: {exc}")
            continue
        if stat.S_ISLNK(mode):
            errors.append(f"release contains a symlink: {relative}")
            continue
        if stat.S_ISDIR(mode):
            continue
        if not stat.S_ISREG(mode):
            errors.append(f"release contains a non-regular file: {relative}")
            continue
        try:
            digest, _ = sha256_contained_release_file(root, relative)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        hashes[relative] = digest
    return hashes, errors


def render_release_checksums(repo: Path) -> str:
    hashes, errors = release_hashes(repo)
    if errors:
        raise ValueError("; ".join(errors))
    return "\n".join(f"{digest}  {relative}" for relative, digest in sorted(hashes.items())) + "\n"


def validate_release_checksums(repo: Path) -> list[str]:
    try:
        checksum_bytes, _ = read_contained_release_file(repo, CHECKSUM_FILE)
    except ValueError as exc:
        return [f"unsafe {CHECKSUM_FILE}: {exc}"]
    expected, errors = release_hashes(repo)
    seen: set[str] = set()
    actual: dict[str, str] = {}
    try:
        checksum_text = checksum_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        return errors + [f"unsafe {CHECKSUM_FILE}: invalid UTF-8: {exc}"]
    for line_number, line in enumerate(checksum_text.splitlines(), start=1):
        match = CHECKSUM_LINE_RE.fullmatch(line)
        if not match:
            errors.append(f"{CHECKSUM_FILE} line {line_number} is malformed")
            continue
        digest, relative = match.groups()
        try:
            _, parts = _release_relative_parts(relative)
        except ValueError:
            errors.append(f"{CHECKSUM_FILE} line {line_number} has an unsafe path")
            continue
        if relative == CHECKSUM_FILE or any(part in CHECKSUM_EXCLUDED_PARTS for part in parts):
            errors.append(f"{CHECKSUM_FILE} line {line_number} has an unsafe path")
            continue
        if relative in seen:
            errors.append(f"{CHECKSUM_FILE} duplicates {relative}")
            continue
        seen.add(relative)
        actual[relative] = digest
    missing = sorted(set(expected) - set(actual))
    unexpected = sorted(set(actual) - set(expected))
    if missing:
        errors.append(f"{CHECKSUM_FILE} is missing entries: {', '.join(missing)}")
    if unexpected:
        errors.append(f"{CHECKSUM_FILE} has unexpected entries: {', '.join(unexpected)}")
    for relative in sorted(set(expected) & set(actual)):
        if expected[relative] != actual[relative]:
            errors.append(f"checksum mismatch: {relative}")
    return errors


def write_release_checksums(repo: Path, content: str) -> None:
    """Atomically replace a regular SHA256SUMS file without following a symlink."""
    root = _release_root(repo)
    checksum_path = root / CHECKSUM_FILE
    try:
        existing_mode = checksum_path.lstat().st_mode
    except FileNotFoundError:
        existing_mode = None
    except OSError as exc:
        raise ValueError(f"cannot inspect {CHECKSUM_FILE}: {exc}") from exc
    if existing_mode is not None and not stat.S_ISREG(existing_mode):
        raise ValueError(f"refusing non-regular {CHECKSUM_FILE}")

    root_descriptor = -1
    temporary = f".{CHECKSUM_FILE}.tmp-{secrets.token_hex(8)}"
    temporary_created = False
    try:
        root_descriptor = os.open(root, _release_open_flags(directory=True))
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
        if hasattr(os, "O_CLOEXEC"):
            flags |= os.O_CLOEXEC
        descriptor = os.open(temporary, flags, 0o644, dir_fd=root_descriptor)
        temporary_created = True
        try:
            remaining = memoryview(content.encode("utf-8"))
            while remaining:
                written = os.write(descriptor, remaining)
                remaining = remaining[written:]
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        os.replace(temporary, CHECKSUM_FILE, src_dir_fd=root_descriptor, dst_dir_fd=root_descriptor)
        temporary_created = False
        os.fsync(root_descriptor)
    except OSError as exc:
        raise ValueError(f"cannot write {CHECKSUM_FILE} safely: {exc}") from exc
    finally:
        if root_descriptor != -1:
            if temporary_created:
                try:
                    os.unlink(temporary, dir_fd=root_descriptor)
                except FileNotFoundError:
                    pass
            os.close(root_descriptor)


def validate_evaluation_assets(repo: Path) -> list[str]:
    """Run the fixture validator without treating it as a completed agent evaluation."""
    script = repo / "scripts" / "validate_evaluation_suite.py"
    if not script.is_file():
        return ["missing scripts/validate_evaluation_suite.py"]
    specification = importlib.util.spec_from_file_location("release_evaluation_validator", script)
    if specification is None or specification.loader is None:
        return ["cannot load scripts/validate_evaluation_suite.py"]
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module.validate(repo)


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        raise ValueError("missing opening frontmatter delimiter")
    parts = text.split("---\n", 2)
    if len(parts) != 3:
        raise ValueError("missing closing frontmatter delimiter")

    metadata: dict[str, str] = {}
    for line in parts[1].splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            raise ValueError(f"invalid frontmatter line: {line!r}")
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"')
    return metadata, parts[2]


def validate_skill(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        return ["missing SKILL.md"]

    text = skill_file.read_text(encoding="utf-8")
    try:
        metadata, body = parse_frontmatter(text)
    except ValueError as exc:
        return [str(exc)]

    expected_fields = {"name", "description"}
    extra = set(metadata) - expected_fields
    missing = expected_fields - set(metadata)
    if extra:
        errors.append("unsupported frontmatter fields: " + ", ".join(sorted(extra)))
    if missing:
        errors.append("missing frontmatter fields: " + ", ".join(sorted(missing)))

    name = metadata.get("name", "")
    description = metadata.get("description", "")
    if name != skill_dir.name:
        errors.append(f"frontmatter name {name!r} does not match folder {skill_dir.name!r}")
    if not NAME_RE.fullmatch(name):
        errors.append("name must contain lowercase letters, digits, and single hyphens only")
    if not description:
        errors.append("description is empty")
    if len(description) > 1024:
        errors.append("description exceeds 1024 characters")
    if "TODO" in text:
        errors.append("SKILL.md contains TODO")
    if len(text.splitlines()) > 500:
        errors.append("SKILL.md exceeds 500 lines")

    for raw_path in RESOURCE_RE.findall(body):
        resource = raw_path.rstrip(".,:;")
        if "<" not in resource and not (skill_dir / resource).exists():
            errors.append(f"referenced resource does not exist: {resource}")

    ui_file = skill_dir / "agents" / "openai.yaml"
    if not ui_file.is_file():
        errors.append("missing agents/openai.yaml")
    else:
        errors.extend(validate_openai_yaml(ui_file, name))

    return errors


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    skills_root = repo / "skills"
    failures = 0

    for error in validate_release_documents(repo):
        failures += 1
        print(f"FAIL: {error}")

    for error in validate_workflow_security(repo):
        failures += 1
        print(f"FAIL: {error}")

    for error in validate_specialist_invocation_boundaries(repo):
        failures += 1
        print(f"FAIL: {error}")

    for error in validate_v2_owner_protection_spine(repo):
        failures += 1
        print(f"FAIL: {error}")

    for error in validate_release_checksums(repo):
        failures += 1
        print(f"FAIL: {error}")

    for error in validate_evaluation_assets(repo):
        failures += 1
        print(f"FAIL: {error}")

    if not skills_root.is_dir():
        print("FAIL: skills directory is missing")
        return 1

    actual_skills = {path.name for path in skills_root.iterdir() if path.is_dir()}
    missing = EXPECTED_SKILLS - actual_skills
    unexpected = actual_skills - EXPECTED_SKILLS
    if missing:
        failures += 1
        print("FAIL: missing skills: " + ", ".join(sorted(missing)))
    if unexpected:
        failures += 1
        print("FAIL: unexpected skills: " + ", ".join(sorted(unexpected)))

    for skill_name in sorted(EXPECTED_SKILLS & actual_skills):
        errors = validate_skill(skills_root / skill_name)
        if errors:
            failures += 1
            print(f"FAIL: {skill_name}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"PASS: {skill_name}")

    if failures:
        print(f"\nFAIL: {failures} validation issue(s) found.")
        return 1

    print(f"\nPASS: {len(EXPECTED_SKILLS)} skills and release documents validated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
