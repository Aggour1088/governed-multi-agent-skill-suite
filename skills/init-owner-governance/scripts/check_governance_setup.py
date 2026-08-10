#!/usr/bin/env python3
"""Check that a project has one usable owner-governed delivery control plane."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BEGIN = "<!-- OWNER-GOVERNED DELIVERY: BEGIN -->"
END = "<!-- OWNER-GOVERNED DELIVERY: END -->"
HOSTS = [
    Path("AGENTS.md"),
    Path("CLAUDE.md"),
    Path(".github/copilot-instructions.md"),
]


def check_adapter(path: Path) -> list[str]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    if text.count(BEGIN) != 1 or text.count(END) != 1:
        errors.append(f"{path}: must contain one complete governance adapter block")
    if ".governance/owner-governed-delivery.md" not in text:
        errors.append(f"{path}: adapter must point to canonical constitution")
    if "$orchestrate-owner-governed-delivery" not in text:
        errors.append(f"{path}: adapter must name the orchestrator")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    args = parser.parse_args()
    root = args.project_root.resolve()
    errors: list[str] = []

    policy = root / ".governance/owner-governed-delivery.md"
    if not policy.is_file():
        errors.append(f"missing canonical constitution: {policy}")
    elif "Owner-Governed Delivery Constitution" not in policy.read_text(encoding="utf-8"):
        errors.append(f"constitution marker missing: {policy}")

    agents = root / "AGENTS.md"
    if not agents.exists():
        errors.append(f"missing required Codex adapter: {agents}")

    for rel in HOSTS:
        errors.extend(check_adapter(root / rel))

    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"PASS: governed setup is structurally valid at {root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
