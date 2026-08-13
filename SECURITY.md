# Security Policy

## Security boundary

This repository contains operating procedures and deterministic local validators. It does **not** provide host-level identity authentication, cryptographic agent attestation, access control for explicit skill invocation, credential storage, or automatic production authorization.

The v2.0.0-rc.1 standalone validator commands **do not accept self-declared execution records** at any risk level. A record may use `declared-passed` only as an untrusted declaration; it is never a verified test or review result. `--integrity-only` can lint contained-file hashes, timestamps, fingerprints, and declared-role consistency, but it does not prove that a command ran, authenticate an identity, or authorize technical acceptance. A trusted host integration must perform those actions outside this raw standalone suite.

The optional local evidence runner can create an E1 reproducible receipt for an exact contract-allowed command. Its host-controlled signed mode can produce an E2 receipt only when the configured host protects the signing key and binds execution to that host. Neither mode proves independent agent identity, broader host enforcement, secure deployment, or E3/E4 assurance. Treat its redaction as a defense-in-depth output safeguard, not permission to place secrets in commands or logs.

## Reporting a vulnerability

Do not post credentials, private repositories, personal data, or active exploit details in a public issue.

Use GitHub's private security-advisory reporting for this repository when it is enabled. If that route is unavailable, contact the repository owner through their GitHub profile with a minimal, non-sensitive summary and request a private reporting channel before sharing reproductions or logs.

Include:

- the affected version, tag, or commit;
- a minimal non-destructive reproduction;
- impact and affected files or workflow;
- whether the issue can cause an unsafe claim, an external write, or exposure of evidence.

## Supported release posture

Only a versioned release whose non-mutating checksum verification passes is suitable for distribution testing. Checksums detect content drift; they are not proof of author identity and are not a substitute for a release signed by the repository owner's signing key.
