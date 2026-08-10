# Architecture Decision Checklist

## Start with evidence

Inspect the actual codebase, schema, infrastructure, integrations, operating constraints, and existing decisions. Do not design from a blank diagram when a real system exists.

## Evaluate every material decision

- Which requirement and constraint does it satisfy?
- What owns state and permission enforcement?
- What happens on duplicate request, concurrency, timeout, retry, partial failure, or recovery?
- How does it preserve compatibility and historical truth?
- What evidence proves scale, latency, availability, and recovery claims?
- How is it observed, migrated, rolled back, or retired?
- Why is the simpler alternative insufficient?

## Escalate

Return to the owner through the orchestrator when a technical discovery changes cost, workflow, privacy, security, data retention, user experience, scope, or release risk.
