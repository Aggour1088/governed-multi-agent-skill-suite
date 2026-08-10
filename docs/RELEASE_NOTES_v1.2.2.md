# v1.2.2 Documentation and Installation Hardening

**Status:** Locally validated release candidate. It is not yet a published GitHub release.

## What changed

- Replaced broad claims that the workflow is host-enforced, role-independent, or identity-verified with the actual instruction and validator boundary.
- Clarified that the orchestrator is the recommended owner-facing entry point, while explicit specialist invocation remains possible at the host level.
- Marked the v1.2 Foundation as a historical design reference because this distribution contains no completed approval record for it.
- Rewrote installation for technical users and authorized AI agents only. It now identifies the supported POSIX/Git/Python/Codex prerequisites and excludes ordinary ChatGPT web installation.
- Replaced the manual copy block with `scripts/install_repo_skills.py`. The installer validates the source, requires a Git repository root, refuses collisions, copies through a temporary directory, and verifies every installed file matches the source.
- Separated consumer checksum verification from the release-maintainer-only checksum regeneration command. `--write` now requires an explicit `--release-maintainer` acknowledgment.

## What this candidate does not claim

- It does not prove a live Codex host has discovered the installed skills; `/skills` in the target host remains the discovery check.
- It does not prove that two declared roles were separate agents or authenticate an identity, command execution, GitHub account, or release archive.
- It does not make the raw folders installable in ChatGPT Work on the web. A separately packaged and permitted plugin is required for that surface.
- It does not contain project-specific source, credentials, or an approved Foundation record.

## Required release gate

Before publishing, run the non-mutating checksum verification, suite validator, evaluation-fixture validator, unit tests, compilation, and the clean repository installation test. Follow [Release Integrity](RELEASE_INTEGRITY.md) for the exact tag and publication order.
