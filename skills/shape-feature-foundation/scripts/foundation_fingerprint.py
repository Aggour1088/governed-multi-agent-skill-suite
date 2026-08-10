#!/usr/bin/env python3
"""Stamp or verify the substantive content fingerprint of a Feature Foundation."""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

EXCLUDED = {
    "status",
    "updated",
    "review_fingerprint",
    "approved_by",
    "approved_on",
    "approval_evidence",
    "approval_fingerprint",
}
FINAL_HEADING = "## 20. Final artifact approval"
FINGERPRINT = re.compile(r"^sha256:[0-9a-f]{64}$")


def split_document(text: str) -> tuple[dict[str, str], str]:
    normalized = text.replace("\r\n", "\n")
    if not normalized.startswith("---\n"):
        raise ValueError("missing opening frontmatter")
    parts = normalized.split("---\n", 2)
    if len(parts) != 3:
        raise ValueError("missing closing frontmatter")
    meta: dict[str, str] = {}
    for line in parts[1].splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"invalid frontmatter line: {line!r}")
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip().strip('"').strip("'")
    return meta, parts[2]


def canonical_content(text: str) -> str:
    meta, body = split_document(text)
    values = [f"{key}={meta[key].strip()}" for key in sorted(meta) if key not in EXCLUDED]
    substantive = body.split(FINAL_HEADING, 1)[0]
    normalized = "\n".join(line.rstrip() for line in substantive.splitlines()).strip()
    return "\n".join(values) + "\n---\n" + normalized + "\n"


def calculate(text: str) -> str:
    return "sha256:" + hashlib.sha256(canonical_content(text).encode("utf-8")).hexdigest()


def replace_value(text: str, key: str, value: str) -> str:
    pattern = re.compile(rf"^(?P<key>{re.escape(key)}:\s*).*$", re.MULTILINE)
    if not pattern.search(text):
        raise ValueError(f"missing frontmatter field: {key}")
    return pattern.sub(lambda match: f'{match.group("key")}"{value}"', text, count=1)


def verify(text: str) -> list[str]:
    meta, _ = split_document(text)
    current = calculate(text)
    errors: list[str] = []
    review = meta.get("review_fingerprint", "")
    approval = meta.get("approval_fingerprint", "")
    if not FINGERPRINT.fullmatch(review):
        errors.append("review_fingerprint is missing or malformed")
    elif review != current:
        errors.append("review_fingerprint does not match current substantive content")
    if meta.get("status") == "APPROVED_FOR_SPECIFICATION":
        if not FINGERPRINT.fullmatch(approval):
            errors.append("approval_fingerprint is missing or malformed")
        elif approval != current:
            errors.append("approval_fingerprint does not match current substantive content")
        if review and approval and review != approval:
            errors.append("approval_fingerprint differs from the reviewed fingerprint")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("foundation", type=Path)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--stamp-review", action="store_true")
    action.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    try:
        text = args.foundation.read_text(encoding="utf-8")
        meta, _ = split_document(text)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"FAIL: {exc}")
        return 1

    if args.stamp_review:
        if meta.get("status") != "FINAL_OWNER_REVIEW":
            print("FAIL: --stamp-review requires FINAL_OWNER_REVIEW")
            return 1
        fingerprint = calculate(text)
        args.foundation.write_text(replace_value(text, "review_fingerprint", fingerprint), encoding="utf-8")
        print(f"STAMPED: {fingerprint}")
        return 0
    if args.verify:
        errors = verify(text)
        if errors:
            print("FAIL")
            for error in errors:
                print(f"- {error}")
            return 1
        print(f"PASS: {calculate(text)}")
        return 0
    print(calculate(text))
    return 0


if __name__ == "__main__":
    sys.exit(main())
