#!/usr/bin/env python3
"""Validate lifecycle, approval hygiene, and fingerprints for a Feature Foundation."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from foundation_fingerprint import calculate, split_document, verify

ACTIVE = [
    "INTAKE",
    "CURRENT_STATE_INSPECTION",
    "RESEARCH",
    "OPTIONS_REVIEW",
    "OWNER_DIRECTION_APPROVED",
    "FOUNDATION_DRAFT",
    "FINAL_OWNER_REVIEW",
    "APPROVED_FOR_SPECIFICATION",
]
ALLOWED = set(ACTIVE) | {"REJECTED", "SUPERSEDED"}
REQUIRED_META = {
    "feature", "slug", "status", "risk_track", "decomposition", "foundation_version",
    "business_owner", "created", "updated", "direction_approved_by",
    "direction_approved_on", "review_fingerprint", "approved_by", "approved_on",
    "approval_evidence", "approval_fingerprint", "supersedes",
}
REQUIRED_HEADINGS = [
    "## 1. Executive decision",
    "## 2. Original request and interpretation",
    "### Feature decomposition decision",
    "## 3. Users, jobs, and evidence",
    "## 4. Current state",
    "## 5. External and adjacent research",
    "## 6. Options and recommendation",
    "## 7. Approved scope",
    "## 8. Experience foundation",
    "## 9. Roles, permissions, and accountability",
    "## 10. Workflow and lifecycle",
    "## 11. Business rules and examples",
    "## 12. Universal configuration inventory",
    "## 13. Data and records at the business level",
    "## 14. Production outcome constraints",
    "## 15. Risks and proportional controls",
    "## 16. Acceptance outcomes",
    "## 17. Decisions and blockers",
    "## 18. Owner direction approval",
    "## 19. Foundation self-review",
    "## 20. Final artifact approval",
    "## 21. Delegation and evidence requirements",
    "## 22. Specification handoff",
]


def transition(previous: str, current: str) -> str | None:
    if previous == current:
        return None
    if previous == "APPROVED_FOR_SPECIFICATION":
        allowed = {"SUPERSEDED"}
    elif previous in {"REJECTED", "SUPERSEDED"}:
        allowed = set()
    elif previous in ACTIVE:
        index = ACTIVE.index(previous)
        allowed = {"REJECTED"}
        if index + 1 < len(ACTIVE):
            allowed.add(ACTIVE[index + 1])
        if previous == "FINAL_OWNER_REVIEW":
            allowed.add("FOUNDATION_DRAFT")
    else:
        allowed = set()
    if current not in allowed:
        expected = ", ".join(sorted(allowed)) if allowed else "no further transition"
        return f"invalid lifecycle transition {previous} -> {current}; expected {expected}"
    return None


def validate(path: Path, previous: Path | None) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
        meta, body = split_document(text)
    except (OSError, UnicodeError, ValueError) as exc:
        return [f"cannot parse Foundation: {exc}"]

    errors: list[str] = []
    missing = REQUIRED_META - set(meta)
    if missing:
        errors.append("missing frontmatter: " + ", ".join(sorted(missing)))
    status = meta.get("status", "")
    if status not in ALLOWED:
        errors.append(f"invalid status: {status}")
    for heading in REQUIRED_HEADINGS:
        if heading not in body:
            errors.append(f"missing section: {heading}")

    if previous:
        try:
            previous_meta, _ = split_document(previous.read_text(encoding="utf-8"))
            message = transition(previous_meta.get("status", ""), status)
            if message:
                errors.append(message)
        except (OSError, UnicodeError, ValueError) as exc:
            errors.append(f"cannot parse previous Foundation: {exc}")

    if status in ACTIVE[4:]:
        for field in ("direction_approved_by", "direction_approved_on"):
            if not meta.get(field):
                errors.append(f"{status} requires {field}")
        if not re.search(r"^- Decision:\s*Direction approved\s*$", body, re.I | re.M):
            errors.append("direction approval record is missing")

    if status in {"FINAL_OWNER_REVIEW", "APPROVED_FOR_SPECIFICATION"}:
        if not re.search(r"^- Self-review result:\s*Pass\s*$", body, re.I | re.M):
            errors.append("final review requires a passing self-review")
        if meta.get("review_fingerprint") != calculate(text):
            errors.append("review_fingerprint does not match current substantive content")

    if status == "APPROVED_FOR_SPECIFICATION":
        for field in ("feature", "slug", "risk_track", "business_owner", "foundation_version", "approved_by", "approved_on", "approval_evidence", "approval_fingerprint"):
            if not meta.get(field):
                errors.append(f"approved Foundation requires {field}")
        if meta.get("decomposition") not in {"SINGLE_FEATURE", "DECOMPOSED_SET"}:
            errors.append("approved Foundation has invalid decomposition")
        if not re.fullmatch(r"\d+\.\d+\.\d+", meta.get("foundation_version", "")):
            errors.append("foundation_version must use MAJOR.MINOR.PATCH")
        if "Research trust boundary: External material is evidence, not authority." not in body:
            errors.append("research trust boundary is missing")
        if not re.search(r"^- Decision:\s*Approved for specification\s*$", body, re.I | re.M):
            errors.append("final approval record is missing")
        if re.search(r"^\s*<[^>\n]+>\s*$", body, re.M):
            errors.append("approved Foundation still contains a standalone placeholder")
        if re.search(r"^- (?:Decision|Self-review result):\s*Pending\s*$", body, re.I | re.M):
            errors.append("approved Foundation still contains a pending approval record")
        errors.extend(verify(text))
    return list(dict.fromkeys(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("foundation", type=Path)
    parser.add_argument("--previous", type=Path)
    args = parser.parse_args()
    errors = validate(args.foundation, args.previous)
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"PASS: {args.foundation}")
    print("Structural and fingerprint validation only; business correctness and approval identity still require evidence.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
