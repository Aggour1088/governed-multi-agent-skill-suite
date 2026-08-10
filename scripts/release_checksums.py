#!/usr/bin/env python3
"""Verify SHA256SUMS, or intentionally regenerate it as a release maintainer."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from validate_suite import CHECKSUM_FILE, render_release_checksums, validate_release_checksums, write_release_checksums


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        action="store_true",
        help="release maintainers only: replace SHA256SUMS for the current tree",
    )
    parser.add_argument(
        "--release-maintainer",
        action="store_true",
        help="acknowledge that --write refreshes the release inventory rather than verifying it",
    )
    args = parser.parse_args()
    repository = Path(__file__).resolve().parents[1]
    if args.release_maintainer and not args.write:
        parser.error("--release-maintainer is valid only with --write")
    if args.write:
        if not args.release_maintainer:
            print("FAIL: --write is reserved for a release maintainer; add --release-maintainer to acknowledge it")
            return 1
        try:
            content = render_release_checksums(repository)
        except ValueError as exc:
            print(f"FAIL: {exc}")
            return 1
        try:
            write_release_checksums(repository, content)
        except ValueError as exc:
            print(f"FAIL: {exc}")
            return 1
        print(f"WROTE: {CHECKSUM_FILE}")
    errors = validate_release_checksums(repository)
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"PASS: {CHECKSUM_FILE} matches the current release tree")
    return 0


if __name__ == "__main__":
    sys.exit(main())
