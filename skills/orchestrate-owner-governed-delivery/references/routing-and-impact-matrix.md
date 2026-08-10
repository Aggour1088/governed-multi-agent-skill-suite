# Routing and Impact Matrix

Route by deliverable and risk, not by a generic claim of expertise.

| Change signal | Minimum procedures |
| --- | --- |
| New outcome or disputed business rule | Foundation, specification, plan |
| Screen, form, dashboard, owner setting, user workflow | Human-centered experience, frontend, QA UI/UX audit |
| API, data rule, transaction, migration, background job | Architecture, backend/data, QA |
| Authentication, authorization, sensitive data, external input | Security, backend/data, QA |
| Performance, cache, bulk processing, worker, recovery | Reliability, backend/data, QA |
| Defect or unexpected behavior | Root-cause debugging, relevant implementer, QA |
| Release or production change | Release verification plus applicable security/reliability |

Require 'guard-approved-artifacts' before execution and 'verify-implementation' before a completion claim. Assign separate tester and reviewer on every package.
