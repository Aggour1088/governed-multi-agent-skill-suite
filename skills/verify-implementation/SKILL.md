---
name: verify-implementation
description: Verify provenance, freshness, traceability, fingerprints, identities, raw evidence, and unresolved limitations before a governed completion claim. Use after independent testing and review, before technical acceptance, release readiness, or when an agent claims a work package is complete.
---

# Verify Implementation Evidence

## Direct invocation boundary

This procedure may modify a governed project only after the orchestrator supplies a validated assignment contract. If invoked directly without that contract, provide only a bounded read-only consultation, return control to `$orchestrate-owner-governed-delivery`, and do not modify a project, accept work, release, or communicate an owner decision. Do not call a direct or sequential pass independent unless a trusted host attests distinct principals; otherwise label it `separate-pass-not-independent`. This behavioral gate does not itself create host-level access control.

Audit proof rather than implementation. Distinguish evidence that is proven, supported, unavailable, stale, contradicted, or failed. Do not edit code, create test results, accept work, or make owner decisions.

During active governed delivery, receive all raw records through $orchestrate-owner-governed-delivery and return an evidence decision.

## Procedure

1. Verify work-package ID, approved inputs, current implementation fingerprint, role identities, independence label, permissions, risk, and required specialist checks.
2. Inspect raw commands, outputs, reports, timestamps, test data, environment, diff, artifacts, and issue status. Treat summaries and screenshots as secondary evidence.
3. Use `scripts/verify_evidence_record.py <record.json> --project-root <project-root>` as a technical-acceptance blocker: a raw standalone record cannot prove that its declared command ran. Use the explicit `--integrity-only` mode only to lint missing fields, overlapping declared identities, stale records, hash mismatches, invalid timestamps, and claimed verified passes. It proves contained-file integrity, not command execution or the real-world identity behind a self-entered string.
4. Map each approved requirement and acceptance criterion to at least one appropriate current evidence source.
5. Confirm that corrections updated the implementation fingerprint and caused affected checks to rerun.
6. Record limitations, unavailable evidence, condition ownership, containment, deadlines, and release implications.
7. Return a Conditional or Fail result for any self-declared raw record. Return Verified Pass only when a trusted host integration independently supplies and verifies execution and identity attestation. Conditional does not become a hidden pass.

## Evidence labels

- Proven: directly inspected or executed with reproducible evidence. A raw standalone validator can prove file integrity and freshness only; it cannot prove agent identity or host attestation.
- Supported: strong evidence exists, but a named required condition remains unavailable.
- Unavailable: no sufficient evidence exists.
- Stale: evidence targets an older fingerprint or invalidated input.
- Failed: observed behavior contradicts requirement.
- Not applicable: justified explicitly.

## V2 contract and evidence boundary

Route this work through `$using-governed-suite` and the current v2 contract. Classify material statements as **Verified**, **Reproducible**, **Reported**, **Inferred**, **Unknown**, or **Failed**. Only an allowed E2+ host or CI receipt may support **Verified**; a raw self-declared record remains **Reported** or **Reproducible**. Stop if provenance, identity limits, scope, or evidence freshness is missing or stale.

## Resources

- 'assets/implementation-evidence-template.md' — evidence decision.
- 'references/evidence-provenance-checklist.md' — evidence and freshness rules.
- 'scripts/verify_evidence_record.py' — record validator.
