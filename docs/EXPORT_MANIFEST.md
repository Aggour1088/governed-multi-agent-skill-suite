# Export Manifest

## Release identity

- Name: Governed Multi-Agent Skill Suite
- Version: 2.0.0-rc.1
- Export date: 2026-08-13
- Source: release source tree; validation results are checked separately and are not embedded proof artifacts
- Publication status: a matching GitHub versioned tag and Release page establish publication; this manifest does not assert whether either exists
- License: Apache License 2.0

## Contents

- 24 portable skills under `skills/`, each stored under its semantic skill name.
- The v2 owner-protection foundation, capability matrix, and no-overwrite upgrade path under `docs/v2/`.
- The v1.2 Feature Foundation design reference in `FEATURE_FOUNDATION_v1.2.md`; no completed approval record is included.
- The supported [installation and verification guide](../INSTALL.md).
- A structural validator, a repository-scope installer, no-dependency tests, and a GitHub Actions workflow.
- `SHA256SUMS`, a security policy, and a release-integrity guide that distinguish checksummed content from a signed release.
- Eighteen adversarial evaluation fixtures under `evaluations/`; they are intentionally marked `not-run` until fresh-context host evidence is stored. This is a release candidate, not a claim that v2 behavior has been evaluated on a live host/model configuration.
- An optional local evidence runner under `adapters/`; it provides bounded receipts but is not a production host adapter, identity provider, or deployment controller.
- No project-specific source files, database exports, credentials, or user data.

## Integrity policy

Obtain a versioned tag or exact reviewed commit, then run `python3 scripts/release_checksums.py` and `python3 scripts/validate_suite.py` after downloading or copying the suite. Do not use `--write` as an installer; it regenerates the inventory for a release maintainer. The validator is intentionally strict: an extra, missing, or renamed skill is a validation failure until the release manifest and tests are deliberately updated.

The package is intended for technical source distribution. It is not an automatic installer or a plugin package. Preserve the `skills/<skill-name>/` folders exactly when using the supported local Codex route, and follow [INSTALL.md](../INSTALL.md) rather than relying on a generic import note. ChatGPT Work on the web requires a separately packaged and permitted plugin; this export does not provide one. See [Release Integrity](RELEASE_INTEGRITY.md): checksums detect content drift but are not an author identity or signature.
