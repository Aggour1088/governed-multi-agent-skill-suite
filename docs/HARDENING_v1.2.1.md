# v1.2.1 Hardening Work Package

## Recorded scope (historical)

- This document records the intended scope and decisions for the v1.2.1 hardening work. It is not an independently verifiable authorization or acceptance record.
- **Risk track:** Enhanced (recorded design intent).
- **Target:** this skill-suite repository only.
- **Excluded:** EduSight attachments, product code, credentials, external integrations, and any claim that raw skills can create host-level access control.

## Outcome

Release a reviewable v1.2.1 patch that makes the suite fail closed where it previously accepted self-declared proof, hardens local file reads and writes, pins the CI supply chain, and documents the remaining platform boundary honestly.

## Engineering decisions

1. A standalone validator may lint file integrity, canonical paths, timestamps, fingerprints, and declared-role consistency. It cannot prove that a command ran or that an arbitrary identifier represents a separate agent. Therefore its default command must never certify a self-declared completion record; `--integrity-only` reports only structural consistency.
2. `host-attested-independent` remains unavailable to the raw standalone validators unless a host-specific, trusted attestation integration is added outside this repository. All raw records use `declared-passed` as an untrusted status, and all risk tracks remain blocked for technical acceptance by the default validator.
3. Evidence must be a regular, non-symlinked file inside an explicit project root, with a recomputed SHA-256, a structured command, exit code, executor-role binding, strict UTC timestamp, and freshness check. A bare string such as `unverified text` is not evidence.
4. The implementation fingerprint must be recomputed from the declared owned files under the project root. Approved-artifact hashes must likewise be recomputed from canonical, contained paths.
5. Downstream artifacts must bind the Foundation in frontmatter with its canonical path, current content hash, and approval fingerprint. Merely mentioning a fingerprint in prose is invalid.
6. The governance-adapter writer must reject symlinked paths and use fail-closed, descriptor-relative writes on platforms that support them. It must never write through a path that resolves outside the chosen project root.
7. Every non-orchestrator skill must state a direct-invocation boundary: without a validated assignment contract it may only provide a read-only consultation. This is a behavioral guard, not host-level access control.
8. GitHub Actions will use immutable full-SHA action references, minimal permissions, and no persisted checkout credentials. Release documents will distinguish a checksum/tagged release from a cryptographically signed release.

## Acceptance criteria

- Regression tests demonstrate rejection of fabricated evidence hashes, invalid timestamps, stale implementation fingerprints, claimed verified passes, self-declared acceptance, and role overlap in both evidence validators.
- Regression tests demonstrate that an artifact which only contains a Foundation fingerprint is rejected, while a correctly bound artifact passes.
- Regression tests demonstrate that `sync_governance_adapters.py --apply` refuses a symlinked target without modifying the external target.
- Repository validation rejects mutable GitHub Action references and specialists that lack the direct-invocation boundary.
- The ten fresh-context adversarial scenarios are checked in with an explicit `not-run` status; CI rejects a fabricated pass claim without a hashed result artifact.
- The intended release gate runs from a clean worktree and binds the public review branch to the tested commit.

## Explicit limitations

This raw standalone suite cannot independently authenticate agent identities, cryptographically attest execution, prevent a user from explicitly invoking a skill, enforce GitHub organization settings, or create a signed release without the repository owner’s signing key. The patch makes those limits visible and blocks false-positive acceptance instead of representing prompt text as platform security.
