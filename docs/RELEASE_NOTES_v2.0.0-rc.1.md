# v2.0.0-rc.1 Owner-Protection Spine

This release candidate implements the first v2 owner-protection spine:

- 24 portable skills, including first-turn routing, isolated execution, data-change safety, and behavioral evaluation;
- one validated v2 work-package contract and host capability profile;
- Owner Truth Cards and consistent fact/evidence labels;
- safe worktree/ledger and migration-plan validators;
- a local evidence-runner adapter that distinguishes E1 from conditionally host-controlled E2 receipts;
- an 18-scenario fresh-context adversarial evaluation catalogue.

## What this release candidate does not claim

- It is not behaviorally evaluated: the published catalogue is `not-run` until raw results are stored for a named host/model configuration.
- It does not prove host enforcement, agent identity, independent review, a meaningful test, production permission, or CI protection from source files alone.
- Its local runner creates E2 only under the documented external condition that a trusted host controls the HMAC key and evidence store.
- It is not a ChatGPT web plugin and does not change a project or production environment automatically.

Do not call this a final v2.0 release until the foundation acceptance conditions and supported-host behavioral evaluations are complete.
