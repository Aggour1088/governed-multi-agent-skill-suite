---
name: review-governed-change
description: Independently review a governed implementation against approved intent, raw diff, correctness, simplicity, security, accessibility, performance, maintainability, and operational consequences. Use as the reviewer role after independent testing; do not modify the implementation or make the final acceptance decision.
---

# Review Governed Change

## Direct invocation boundary

This procedure may modify a governed project only after the orchestrator supplies a validated assignment contract. If invoked directly without that contract, provide only a bounded read-only consultation, return control to `$orchestrate-owner-governed-delivery`, and do not modify a project, accept work, release, or communicate an owner decision. Do not call a direct or sequential pass independent unless a trusted host attests distinct principals; otherwise label it `separate-pass-not-independent`. This behavioral gate does not itself create host-level access control.

Act as an independent reviewer. Read raw artifacts and the actual change before the implementer's narrative. Evaluate whether the implementation deserves technical acceptance; do not rewrite it yourself.

During active governed delivery, receive a bounded assignment contract from $orchestrate-owner-governed-delivery and return findings only to the orchestrator.

## Procedure

1. Verify reviewer identity differs from implementer and tester, and bind the review to the exact implementation fingerprint.
2. Read the constitution, approved Foundation, UX/specification/architecture/plan as applicable, assignment contract, raw diff, tests, migration/configuration, and prior findings.
3. Check scope fidelity, protected behavior, correctness, error handling, permission enforcement, data integrity, historical behavior, concurrency, recovery, test quality, accessibility, localization, performance, observability, dependency change, documentation, and rollback implications.
4. Prefer the simplest implementation that satisfies approved constraints. Flag unjustified abstraction, duplication, hidden state, bypassed validation, speculative infrastructure, weak tests, and undocumented trade-offs.
5. Classify findings by severity and include file or artifact location, evidence, impact, required correction, and required rerun checks.
6. Do not make edits, rerun a mutable setup that changes the target, approve a failed test, or hide an unverified claim.
7. Return Approve, Approve with documented non-blocking condition, or Request changes. Only the orchestrator can technically accept.

## V2 contract and evidence boundary

Route this work through `$using-governed-suite` and the current v2 contract. Classify material statements as **Verified**, **Reproducible**, **Reported**, **Inferred**, **Unknown**, or **Failed**. Only an allowed E2+ host or CI receipt may support **Verified**; a reviewer report remains **Reported** or **Reproducible** unless the host attests the review mode. Stop if raw diff, role boundary, scope, or evidence freshness is missing or stale.

## Resources

- 'assets/review-report-template.md' — independent review record.
- 'references/governed-review-checklist.md' — review dimensions and severities.
