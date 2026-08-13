# V2 Owner-Protection Foundation

## Status and purpose

This is the implementation foundation for the v2.0.0 source-release line. It turns the suite from a collection of good procedures into a clearer owner-control layer: an AI agent must expose authority, evidence, uncertainty, scope, and recovery before asking a non-programmer to decide.

It does not claim that Markdown instructions alone enforce permissions, verify a command, prove separate identities, or protect production.

## Product outcome

An owner can direct a software change from idea through delivery and receive one plain-language decision at a time. The system makes unsupported claims visible, challenges unsafe proposed solutions, prevents silent scope expansion in its documented workflow, and records the limits of the host actually in use.

## Non-goals

- Do not turn every question or typo into enterprise ceremony.
- Do not claim a local skill can enforce a host sandbox, identity, CI, or deployment rule.
- Do not make multi-agent role names look independent without trusted host evidence.
- Do not prescribe microservices, queues, caches, SLO targets, or infrastructure without workload evidence.
- Do not allow the owner to approve raw code or jargon instead of business impact and risk.

## Core decisions

| Decision | v2 rule |
| --- | --- |
| Entry point | `$using-governed-suite` is the lightweight first-turn router. Automatic activation is best-effort only; explicit invocation or a project adapter remains the reliable route. |
| Owner experience | Every material decision uses an Owner Truth Card: decision, outcome, current state, recommendation, alternative, scope, risk, cost/time, evidence, recovery, and stop conditions. |
| Evidence | Material statements are labelled Verified, Reproducible, Reported, Inferred, Unknown, or Failed. Labels never become stronger because an agent sounds confident. |
| Mutating work | A current v2 work-package contract identifies scope, authority, sources, roles, evidence, operations, economics, and host capability. It expires and must be refreshed after material drift. |
| Execution | One isolated workspace and durable ledger per work package; ownership conflicts and unlimited correction loops are blockers. |
| Data | Production data changes use expand → backfill → validate → cut over → observe → contract, with recovery evidence. |
| Evaluation | Eighteen fresh-context adversarial scenarios define the required behavior tests. Fixtures are not runtime results. |
| Trusted evidence | The local runner produces E1 by default. A signed E2 receipt is conditional on a trusted host controlling the signing key and evidence store outside agent authority. |

## Assurance model

| Level | Meaning | May support |
| --- | --- | --- |
| E0 | Narrative claim only | No gate pass |
| E1 | Exact command and artifact recorded | Conditional/reproducible investigation |
| E2 | trusted host records execution, revision, output, and exit state | Technical evidence within declared host limits |
| E3 | trusted host also records distinct principal and restricted review mode | An independence claim within host limits |
| E4 | Protected CI/build/deploy provenance | High-risk release evidence |

The suite never upgrades E1 to E2, E2 to E3, or E3 to E4 by wording alone.

## Initial target assurance

The core source package targets compatible Codex CLI/IDE project environments with explicit routing, repository-scoped skills, worktree-capable Git, and Python 3. It is deliberately not a ChatGPT web plugin and does not claim one-click web installation.

The v2.0.0 source has structural and deterministic tests plus a completed E1 fresh-context result set for all 18 maintained scenarios on the named configuration recorded in the [behavior scorecard](BEHAVIOR_SCORECARD_v2.0.0.md). That result does not apply to other hosts, models, capability profiles, or changed source fingerprints. The suite is not production-enforcing until protected CI/deployment and credential boundaries are configured outside the agent workspace.

## Acceptance conditions for a final v2.0 release

1. All 24 skills use the common contract and evidence vocabulary.
2. The Owner Truth Card, risk alerts, source hierarchy, and stop policy are present and validated.
3. The isolated execution, ledger, data-change, evaluation, and evidence-adapter procedures pass deterministic tests.
4. Every advertised host/model configuration has current raw results for all critical adversarial scenarios.
5. The advertised capability matrix and release notes match what the host actually enforces.

## Change control

Any change to a contract schema, evidence label, assurance claim, host capability, or advertised release posture requires a versioned migration note, targeted regression tests, and updated scorecard/capability documentation. A source-only feature must never silently become an enforcement claim.
