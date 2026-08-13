# Governance Artifact Schema

## Required project paths

Use '.governance/owner-governed-delivery.md' as the only policy source. Store feature artifacts under '.governance/features/<feature-id>/'.

Declare actual host limits once at '.governance/capability-profile.json'. This record describes capability; it is not an enforcement grant. Route requests through `$using-governed-suite` before creating a feature artifact.

Create only files that apply:

- 'foundation.md' with review and approval fingerprints;
- 'ux-foundation.md';
- 'specification.md' and 'clarifications.md';
- 'architecture.md' and 'decisions/ADR-*.md';
- 'implementation-plan.md' and 'tasks.md';
- 'assignment-contracts/<task-id>.md';
- 'work-package-contracts/<package-id>.json' using the common v2 contract;
- 'owner-truth-cards/<checkpoint-id>.md' for a material owner decision;
- 'execution-ledgers/<package-id>.json' when isolated execution or resumption is used;
- 'delivery-ledger.jsonl';
- independent test, specialist, review, and evidence reports;
- owner decision packets;
- release, rollback, and observation records.

## Identity rules

Record declared role identity, role, strict UTC timestamp, input fingerprints, output fingerprint, structured command, exit code, contained evidence-file path and SHA-256, result, limitation, and return status. Reject a package when its implementer, tester, or reviewer identity overlaps. Do not describe self-entered identities as independently authenticated; only a trusted host integration can make that assertion.

Label material statements as **Verified**, **Reproducible**, **Reported**, **Inferred**, **Unknown**, or **Failed**. Only a capability-permitted E2+ host or CI receipt supports **Verified**; a plan, agent statement, screenshot, local validator, or self-entered role label does not.

## Artifact status rules

Use explicit statuses. Mark downstream artifacts stale when their approved input changes. Preserve superseded records instead of overwriting historical truth. Treat a missing or unverifiable fingerprint as a blocker, not a pass.
