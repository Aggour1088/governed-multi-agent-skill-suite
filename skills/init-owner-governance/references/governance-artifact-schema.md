# Governance Artifact Schema

## Required project paths

Use '.governance/owner-governed-delivery.md' as the only policy source. Store feature artifacts under '.governance/features/<feature-id>/'.

Create only files that apply:

- 'foundation.md' with review and approval fingerprints;
- 'ux-foundation.md';
- 'specification.md' and 'clarifications.md';
- 'architecture.md' and 'decisions/ADR-*.md';
- 'implementation-plan.md' and 'tasks.md';
- 'assignment-contracts/<task-id>.md';
- 'delivery-ledger.jsonl';
- independent test, specialist, review, and evidence reports;
- owner decision packets;
- release, rollback, and observation records.

## Identity rules

Record declared role identity, role, strict UTC timestamp, input fingerprints, output fingerprint, structured command, exit code, contained evidence-file path and SHA-256, result, limitation, and return status. Reject a package when its implementer, tester, or reviewer identity overlaps. Do not describe self-entered identities as independently authenticated; only a trusted host integration can make that assertion.

## Artifact status rules

Use explicit statuses. Mark downstream artifacts stale when their approved input changes. Preserve superseded records instead of overwriting historical truth. Treat a missing or unverifiable fingerprint as a blocker, not a pass.
