# Planning and Ownership Rules

## Package design

Use vertical, coherent packages. Define one owner-visible objective, fixed scope, owned targets, risks, proof, and rollback implication per package.

## Parallelization

Allow parallel work only after proving that packages do not overlap in files, schema/migrations, API contracts, test fixtures, owner decisions, feature flags, environments, or deployment order. Serialize uncertain work.

## Mandatory evidence

Require distinct implementer, tester, and reviewer identities. Define what each must return before work starts. Include security, reliability, UX, architecture, data, and release checks where impact requires them.

## Milestones

Report work at a meaningful owner-visible package or agreed milestone. Do not create a decision burden around internal formatting or micro-edits.
