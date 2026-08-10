---
name: execute-approved-work
description: Deliver a bounded, owner-approved implementation slice without scope drift. Use only after the artifact gate and safe-workspace preflight pass, when an orchestrator has assigned a work package with clear ownership, evidence requirements, separate testing, and separate review.
---

# Execute Approved Work

## Direct invocation boundary

This procedure may modify a governed project only after the orchestrator supplies a validated assignment contract. If invoked directly without that contract, provide only a bounded read-only consultation, return control to `$orchestrate-owner-governed-delivery`, and do not modify a project, accept work, release, or communicate an owner decision. Do not call a direct or sequential pass independent unless a trusted host attests distinct principals; otherwise label it `separate-pass-not-independent`. This behavioral gate does not itself create host-level access control.

Execute one approved work package at a time. Keep the package connected to its approved inputs and ledger; stop rather than silently widening scope.

Do not act as tester, reviewer, technical acceptor, owner reporter, or release authority for the same package.

## Procedure

1. Verify the active assignment contract, approved fingerprints, preflight record, ownership, permission ceiling, and baseline.
2. Restate the objective, exclusions, acceptance criteria, risk, and stop conditions before editing.
3. Use $develop-test-first for behavioral changes unless an approved exception documents why it is impractical.
4. Make the smallest coherent vertical slice. Preserve existing conventions and unrelated user work.
5. Record each material implementation decision, changed target, command, test result, known limitation, and implementation fingerprint in the delivery ledger.
6. Stop and escalate unexpected architecture, security, data, UX, dependency, scope, permission, or environment findings.
7. Produce self-check evidence only. Do not label the package tested, reviewed, or accepted.
8. Return the exact changed fingerprint, raw evidence, limitations, and next required independent checks to the orchestrator.

## Correction rule

When a tester, reviewer, or specialist finding requires a change, update the implementation fingerprint and mark every affected prior evidence record stale. Return the package through independent testing and review again.

## Resources

- 'assets/implementation-self-check-template.md' — implementer return record.
- 'references/execution-ledger-protocol.md' — slice, ledger, and drift rules.
