---
name: guard-approved-artifacts
description: Independently gate Feature Foundations, UX artifacts, specifications, architecture records, and implementation plans before execution. Use when checking approval fingerprints, lifecycle order, drift, contradictions, missing requirements, task ownership, or scope changes before a governed change begins.
---

# Guard Approved Artifacts

## Direct invocation boundary

This procedure may modify a governed project only after the orchestrator supplies a validated assignment contract. If invoked directly without that contract, provide only a bounded read-only consultation, return control to `$orchestrate-owner-governed-delivery`, and do not modify a project, accept work, release, or communicate an owner decision. Do not call a direct or sequential pass independent unless a trusted host attests distinct principals; otherwise label it `separate-pass-not-independent`. This behavioral gate does not itself create host-level access control.

Audit delivery artifacts without repairing their business meaning. Verify both machine-checkable integrity and semantic consistency. Return material conflict to the appropriate earlier gate through $orchestrate-owner-governed-delivery.

Do not implement code, change artifacts silently, or accept a package.

## Procedure

1. Read the project constitution, approved Foundation, UX Foundation when applicable, specification, architecture, plan, task contracts, and previous gate records.
2. Run 'scripts/check_approved_artifacts.py' with the actual artifact paths.
3. Run the artifact gate with `--project-root`, then verify that each downstream artifact has canonical frontmatter binding the exact Foundation path, current Foundation content hash, and approval fingerprint. A fingerprint merely mentioned in prose is invalid.
4. Check requirements-to-plan traceability, task ownership, non-overlapping writes, role separation, dependencies, evidence, specialist checks, release/recovery coverage, and owner-visible milestones.
5. Identify drift as Critical, High, Medium, or Low. Block on Critical or High drift.
6. Report Pass, Conditional, or Fail. Conditional must name the condition, accountable owner, containment, deadline, and whether execution is allowed.

## Decisions

- Pass: all mandatory inputs are approved, bound, coherent, and executable.
- Conditional: no blocking conflict exists, but a recorded limited condition remains.
- Fail: approval missing, fingerprint stale, scope changed, required evidence absent, role overlap, or a material contradiction exists.

Do not call a conflict resolved merely because a reasonable agent could guess an answer.

## V2 contract and evidence boundary

Route this work through `$using-governed-suite` and the current v2 contract. Classify material statements as **Verified**, **Reproducible**, **Reported**, **Inferred**, **Unknown**, or **Failed**. Only an allowed E2+ host or CI receipt may support **Verified**; an unchecked artifact remains **Unknown**. Stop if approval, scope, contract freshness, or evidence binding is missing or stale.

## Resources

- 'assets/artifact-gate-report-template.md' — gate decision record.
- 'references/artifact-integrity-checklist.md' — semantic review checklist.
- 'scripts/check_approved_artifacts.py' — structural binding checker.
