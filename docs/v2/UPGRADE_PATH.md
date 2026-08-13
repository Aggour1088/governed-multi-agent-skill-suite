# Upgrade Path from v1.2.3

## What changes

v2 adds four skills, a common v2 contract, Owner Truth Cards, a capability profile, isolated-execution ledger controls, data-change safety controls, an 18-scenario evaluation catalogue, and a local evidence-runner adapter. Existing skills retain their lifecycle roles but now use the common evidence labels and contract boundary.

## Safe migration

1. Keep the existing v1.2.3 skill tree intact as a recovery copy.
2. Read the v2 capability matrix and decide whether the host is source-only, local-runner, or protected-CI capable. Do not assume the strongest profile.
3. Use a fresh staging repository or skill scope. The repository installer has a no overwrite policy and intentionally refuses to merge into an existing `.agents/skills` directory.
4. Install and run the v2 validation, checksum, evaluation-catalogue, and project discovery checks in the staging target.
5. Add or update the project constitution using `init-owner-governance`; declare the project capability profile before beginning a v2 work package.
6. Move active work only by creating a v2 contract and ledger that references the actual current repository baseline. Do not reuse stale v1 evidence as a v2 Verified claim.
7. Keep v1.2.3 available until the team validates at least one representative Fast/Standard work package and any relevant Enhanced data/security path.

## Rollback

Restore the preserved v1.2.3 skill directory or remove the separate v2 staging scope. Do not delete the old scope until a named owner accepts the migration result. A suite upgrade cannot rewrite a project constitution, user files, deployment configuration, or evidence records automatically.

## Behavior-evaluation boundary

v2.0.0 has a completed E1 fresh-context evaluation of all 18 maintained scenarios for the exact `chatgpt-codex-gpt-5-6-platform-managed` configuration and the router fingerprint recorded in the [behavior scorecard](BEHAVIOR_SCORECARD_v2.0.0.md). It is not evaluated for other hosts, models, capability profiles, or changed router material, and it does not provide host enforcement or independent-agent identity attestation. Do not replace a production governance path solely because static validation or this one configuration’s scorecard passes.
