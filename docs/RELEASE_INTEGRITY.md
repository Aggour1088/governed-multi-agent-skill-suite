# Release Integrity and Trust Boundary

## Two different operations

`SHA256SUMS` lists a SHA-256 hash for every distributable regular file in a release tree except `SHA256SUMS` itself. There are two deliberately different operations:

| Role | Command | Meaning |
| --- | --- | --- |
| Installer, reviewer, or consumer | `python3 scripts/release_checksums.py` | Verify that the current tree matches its checked-in inventory. This command does not modify the tree. |
| Release maintainer, before tagging | `python3 scripts/release_checksums.py --write --release-maintainer` | Deliberately regenerate the inventory after approved source changes. This command changes `SHA256SUMS`; it is not a verification step for consumers. |

Never use `--write` when checking a downloaded or copied release. It can replace the evidence you intended to verify. The script requires the explicit `--release-maintainer` acknowledgment to reduce accidental misuse, but that flag is not a cryptographic authorization control.

## What a consumer can verify

From an untouched, versioned checkout, run:

```bash
python3 scripts/release_checksums.py
python3 scripts/validate_suite.py
python3 scripts/validate_evaluation_suite.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

These checks show that the current tree matches its checked-in checksum inventory and that the repository's deterministic controls pass. They detect drift from an inventory prepared earlier. They do **not** authenticate a person, model, GitHub account, release archive, command execution, or execution environment.

In particular, checksums retrieved only from the same untrusted source as the tree do not establish an independent chain of trust. A signed tag, a signed checksum asset, or another trusted release-verification path is required before claiming cryptographic provenance.

## Required maintainer publication sequence

1. Start from the reviewed release-candidate tree. Confirm that the intended version and release notes are correct and that no unrelated or generated files are present.
2. Run the full validation sequence above. Correct every failure before proceeding.
3. Regenerate the inventory only if approved content changed:

   ```bash
   python3 scripts/release_checksums.py --write --release-maintainer
   python3 scripts/release_checksums.py
   python3 scripts/validate_suite.py
   python3 -m unittest discover -s tests -p 'test_*.py' -v
   ```

4. Commit the exact release tree, including `SHA256SUMS`, and obtain the required review before creating the tag.
5. At the final merged commit, rerun the consumer verification commands without `--write`. Do not alter the tree after this verification.
6. Create a versioned annotated tag at that exact verified commit, for example `v1.2.2`.
7. Create a GitHub Release from that tag. Attach `SHA256SUMS` and, when produced, an archive built from the same tag.
8. If the release is described as **signed**, the repository owner must sign the tag or checksum with the owner's signing key and publish the corresponding public key or trusted verification path.

## Current limitation

This release candidate is **checksummed, not signed**. Do not imply that an annotated Git tag is cryptographically signed, that checksums authenticate an author, or that a self-declared execution record is verified. The raw standalone suite cannot supply those guarantees.

## GitHub controls

Configure GitHub controls separately from this source tree. A maintainer may protect `main` with a ruleset that blocks force pushes and deletion, requires pull requests, and requires the `Validate skill suite / validate` status check. The repository can validate its workflow configuration, but it cannot enforce GitHub organization or repository settings itself.
