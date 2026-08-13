---
name: debug-from-root-cause
description: Investigate and correct a governed defect through reproducible evidence, causal isolation, minimal correction, and regression proof. Use when behavior is wrong, inconsistent, degraded, or unexplained and a symptom patch would risk hiding the true cause.
---

# Debug From Root Cause

## Direct invocation boundary

This procedure may modify a governed project only after the orchestrator supplies a validated assignment contract. If invoked directly without that contract, provide only a bounded read-only consultation, return control to `$orchestrate-owner-governed-delivery`, and do not modify a project, accept work, release, or communicate an owner decision. Do not call a direct or sequential pass independent unless a trusted host attests distinct principals; otherwise label it `separate-pass-not-independent`. This behavioral gate does not itself create host-level access control.

Diagnose before changing. Fix the cause that explains the evidence; do not stack guesses, blanket retries, or unrelated refactors onto an unexplained failure.

During active governed delivery, work only under a bounded assignment contract. Do not self-review, accept, or describe a fix as independently proven.

## Procedure

1. Capture the expected behavior, observed behavior, impact, affected scope, environment, timestamps, inputs, and safe reproduction steps.
2. Reproduce reliably or state why it cannot yet be reproduced. Preserve raw logs, traces, data shape, and error output without exposing secrets.
3. Localize the failure boundary. Compare a working path with the failing path and reduce the problem to the smallest differentiator.
4. Form one falsifiable hypothesis at a time. Change one variable, collect evidence, and discard or refine the hypothesis.
5. Inspect recent changes, configuration, data, permissions, dependencies, concurrency, timing, and external behavior only as evidence requires.
6. Correct the root cause within approved scope. Use a regression test or equivalent proof that would fail before the correction.
7. Recheck relevant negative, boundary, integration, and recovery behavior. Produce an updated fingerprint and mark older evidence stale.
8. Escalate after repeated failed hypotheses, a suspected architecture flaw, data integrity risk, security concern, or scope change.

## V2 contract and evidence boundary

Route this work through `$using-governed-suite` and the current v2 contract. Classify material statements as **Verified**, **Reproducible**, **Reported**, **Inferred**, **Unknown**, or **Failed**. Only an allowed E2+ host or CI receipt may support **Verified**; a self-written log remains **Reported** or **Reproducible**. Stop if reproduction, scope, authority, or evidence freshness is missing or stale.

## Resources

- 'assets/root-cause-record-template.md' — diagnostic record.
- 'references/root-cause-protocol.md' — reproduction and hypothesis discipline.
