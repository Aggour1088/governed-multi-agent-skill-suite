---
name: coordinate-isolated-agent-execution
description: Coordinate bounded multi-agent implementation in an isolated workspace using an active v2 work-package contract, durable ledger, task briefs, ownership map, cost limits, review boundaries, and a finite correction loop. Use after governed planning and artifact gating, before parallel implementation or when resuming a paused work package.
---

# Coordinate Isolated Agent Execution

Coordinate execution; do not become an unbounded implementation agent, owner approver, deployment authority, or evidence verifier.

## Direct invocation boundary

This procedure may create or change a project workspace only with a current, mutation-authorized v2 assignment contract from `$orchestrate-owner-governed-delivery`. If invoked without that contract, provide a read-only consultation or a draft plan only, and do not modify a project, accept work, release, or communicate an owner decision.

## Procedure

1. Validate the contract with `$using-governed-suite` before creating a workspace or assigning a role.
2. Inspect the actual repository root, baseline revision, uncommitted owner work, active worktrees, and existing ledger. Stop on overlap or uncertainty.
3. Use `scripts/prepare_isolated_workspace.py` in preview mode first. Create a new worktree only from the contract baseline, never on the protected default branch and never by overwriting an existing directory.
4. Create a durable ledger from `assets/execution-ledger.template.json`. Record contract ID, baseline, workspace, task graph, file/interface ownership, role, model/reasoning choice, expected cost, fix-round count, and exact next safe action.
5. Validate the ledger before work and after every material correction with `scripts/validate_execution_ledger.py`.
6. Allow parallel writing only when the ownership matrix proves no file, interface, migration, test fixture, or environment conflict.
7. Give each role one bounded task brief. Tester and reviewer may inspect evidence but must not repair the implementation. Do not call passes independent unless the host has actually attested distinct principals.
8. Stop at the contract’s finite correction limit. Escalate the decision rather than looping or silently changing scope.
9. Before resuming after compaction or handoff, read the ledger and reconcile it with the actual repository state; memory is not authority.

## Evidence and authority labels

Use the v2 labels from `$using-governed-suite`. Ledger contents are **Reported** or **Reproducible** unless a protected host or CI receipt supports a stronger claim. A worktree is blast-radius control, not proof of agent independence.

## Resources

- `assets/execution-ledger.template.json` — durable work-package state.
- `assets/task-brief-template.md` — bounded role brief.
- `assets/ownership-matrix-template.md` — conflict scan record.
- `references/isolated-execution-protocol.md` — workspace, review, and circuit-breaker rules.
- `scripts/prepare_isolated_workspace.py` — preview-first worktree setup.
- `scripts/validate_execution_ledger.py` — ledger and ownership validator.
