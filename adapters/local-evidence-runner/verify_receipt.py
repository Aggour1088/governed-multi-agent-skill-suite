#!/usr/bin/env python3
"""Verify a signed local-evidence-runner receipt and its redacted output artifact."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import stat
import sys
from pathlib import Path


def canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--hmac-key-env", required=True)
    args = parser.parse_args()
    try:
        path = args.receipt.resolve(strict=True)
        if args.receipt.is_symlink() or not stat.S_ISREG(args.receipt.lstat().st_mode):
            raise ValueError("receipt must be a regular file")
        receipt = json.loads(path.read_text(encoding="utf-8"))
        signature = receipt.pop("signature")
        if not isinstance(signature, dict) or signature.get("algorithm") != "hmac-sha256" or not isinstance(signature.get("value"), str):
            raise ValueError("receipt lacks a valid HMAC signature")
        key = os.environ.get(args.hmac_key_env)
        if not key:
            raise ValueError("verification key is unavailable")
        expected = hmac.new(key.encode("utf-8"), canonical_json(receipt), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature["value"]):
            raise ValueError("receipt signature does not match")
        output = receipt.get("output_artifact", {})
        output_path = path.parent / output.get("path", "")
        if output_path.parent != path.parent or output_path.is_symlink() or not output_path.is_file():
            raise ValueError("output artifact is unsafe")
        actual = "sha256:" + hashlib.sha256(output_path.read_bytes()).hexdigest()
        if actual != output.get("sha256"):
            raise ValueError("output artifact hash does not match")
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError, KeyError) as exc:
        print(f"FAIL: {exc}")
        return 1
    print("PASS: signed receipt and redacted output artifact match")
    print("LIMIT: this verifies the HMAC only; E2 also depends on a host-controlled key and evidence store.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
