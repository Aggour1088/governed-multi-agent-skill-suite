---
name: init-owner-governance
description: Initialize or repair an owner-governed multi-agent delivery setup in a software project. Use when adopting this suite, adding an AI host, auditing governance wiring, or creating the canonical constitution and thin host adapters without overwriting existing project rules.
---

# Initialize Owner Governance

## Direct invocation boundary

This procedure may modify a governed project only after the orchestrator supplies a validated assignment contract. If invoked directly without that contract, provide only a bounded read-only consultation, return control to `$orchestrate-owner-governed-delivery`, and do not modify a project, accept work, release, or communicate an owner decision. Do not call a direct or sequential pass independent unless a trusted host attests distinct principals; otherwise label it `separate-pass-not-independent`. This behavioral gate does not itself create host-level access control.

Establish one project-local constitution before governed delivery begins. Treat existing project instructions as user-owned material: inspect, preserve, and reconcile them; never replace them silently.

## Operating boundary

Route ordinary product work to $orchestrate-owner-governed-delivery after setup. Use this skill only to establish, repair, or audit the project control plane.

Do not modify product code, dependencies, infrastructure, deployment configuration, credentials, or project data. Do not initialize a project merely because an unrelated specialist skill is invoked.

## Procedure

1. Locate the repository root and read every applicable project instruction, governance file, host adapter, and documented workflow.
2. Classify each existing instruction as compatible, conflicting, duplicated, unknown, or project-specific.
3. Present conflicts and the smallest safe integration plan to the owner before writing.
4. Create '.governance/owner-governed-delivery.md' from 'assets/owner-governed-delivery-template.md' only when no equivalent constitution exists.
5. Preserve an equivalent existing constitution when it is compatible; propose a deliberate merge when it is not.
6. Create '.governance/capability-profile.json' from `$using-governed-suite`'s capability-profile template only when it is absent. Populate it from observed host capabilities; do not infer enforcement from a configuration file.
7. Run 'scripts/sync_governance_adapters.py <project-root>' without '--apply' to preview thin adapter targets.
8. Apply only the reviewed targets. Keep adapters short and point them to the canonical constitution and router; do not duplicate policy text.
9. Copy only the artifact templates needed for a real feature into '.governance/features/<feature-id>/' when that feature begins. Use the v2 work-package contract and Owner Truth Card from `$using-governed-suite` rather than a second local schema.
10. Run 'scripts/check_governance_setup.py <project-root>' after any change.
11. Explain in plain language what becomes mandatory and what still requires owner approval.

## Required safeguards

- Keep exactly one canonical constitution at the project path above.
- Stop when project rules conflict, a host adapter is malformed, or the project root is uncertain.
- Preserve existing instructions and user changes verbatim outside the marked adapter block.
- Treat host adapters as pointers, never as competing constitutions.
- Do not create empty feature folders only to appear complete.
- Do not call setup complete until the structural check passes.

## V2 contract and evidence boundary

Route this work through `$using-governed-suite` and declare the host capability profile before promising enforcement. Classify material statements as **Verified**, **Reproducible**, **Reported**, **Inferred**, **Unknown**, or **Failed**. Only an allowed E2+ host or CI receipt may support **Verified**; setup files alone remain **Reproducible**. Stop if existing policy conflicts, authority, or migration safety is missing or stale.

## Completion record

Report the constitution path, adapters inspected and changed, preserved instructions, unresolved conflicts, structural-check result, and the next owner-facing action. State clearly that setup creates governance; it does not approve a feature or authorize implementation.

## Resources

- 'assets/owner-governed-delivery-template.md' — canonical project constitution.
- 'assets/project-agent-contract.md' — minimal adapter block.
- 'assets/assignment-contract-template.md' — bounded specialist assignment.
- 'assets/task-acceptance-record-template.md' — technical-acceptance record.
- 'assets/owner-decision-packet-template.md' — plain-language owner packet.
- 'references/governance-artifact-schema.md' — artifact and identity requirements.
- 'scripts/sync_governance_adapters.py' — non-destructive adapter preview and apply.
- 'scripts/check_governance_setup.py' — structural setup check.
- `$using-governed-suite` — common capability profile, work-package contract, and Owner Truth Card.
