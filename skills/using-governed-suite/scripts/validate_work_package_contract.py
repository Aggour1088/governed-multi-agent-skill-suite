#!/usr/bin/env python3
"""Validate a v2 work-package contract without claiming host enforcement."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from contract_rules import load_contract


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract", type=Path)
    args = parser.parse_args()
    try:
        load_contract(args.contract)
    except ValueError as exc:
        print(f"FAIL: {exc}")
        return 1
    print("PASS: contract is structurally current and declares its assurance limits")
    return 0


if __name__ == "__main__":
    sys.exit(main())
