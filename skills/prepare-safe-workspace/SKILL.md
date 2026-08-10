---
name: prepare-safe-workspace
description: Establish a safe, reproducible preflight baseline before a governed implementation changes files, configuration, data, or environments. Use immediately before an approved work package begins or whenever repository state, instructions, permissions, user changes, tools, ownership, or rollback constraints are uncertain.
---

# Prepare Safe Workspace

## Direct invocation boundary

This procedure may modify a governed project only after the orchestrator supplies a validated assignment contract. If invoked directly without that contract, provide only a bounded read-only consultation, return control to `$orchestrate-owner-governed-delivery`, and do not modify a project, accept work, release, or communicate an owner decision. Do not call a direct or sequential pass independent unless a trusted host attests distinct principals; otherwise label it `separate-pass-not-independent`. This behavioral gate does not itself create host-level access control.

Create a factual preflight record before editing. Preserve user work and stop on uncertainty; a clean-looking directory is not proof that a target is safe.

During active governed delivery, work only under an assignment contract and report to $orchestrate-owner-governed-delivery. Do not modify the implementation target.

## Procedure

1. Confirm repository root, applicable instructions, active constitution, feature artifacts, work-package contract, approved fingerprints, risk, and authorized target.
2. Inspect version-control status, current branch or revision, uncommitted user changes, ignored files, nested repositories, generated output, and active worktrees.
3. Run the existing baseline checks without altering the target. Distinguish project failures, environment failures, unavailable tools, and unverified checks.
4. Confirm permitted files, interfaces, databases, environments, credentials, and destructive-action boundaries.
5. Confirm backup, migration, fixture, rollback, and recovery constraints when data or configuration could change.
6. Detect overlap with active work. Prevent parallel edits to the same file, contract, migration, test fixture, or environment.
7. Record exact commands, results, baseline fingerprint, user changes to preserve, and blockers using 'assets/preflight-record-template.md'.
8. Run 'scripts/workspace_preflight.py <project-root>' as a non-mutating structural supplement.

## Stop conditions

Stop and return a blocker for a missing contract, unclear target, unverified approval, user change that could be overwritten, failed baseline without cause, insufficient permission, unresolved conflict, or missing recovery path for higher-risk change.

## Resources

- 'assets/preflight-record-template.md' — preflight record.
- 'references/workspace-safety-checklist.md' — baseline and rollback checks.
- 'scripts/workspace_preflight.py' — non-mutating repository inventory.
