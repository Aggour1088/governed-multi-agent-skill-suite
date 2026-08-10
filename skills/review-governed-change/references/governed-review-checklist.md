# Governed Review Checklist

## Fidelity

- Match approved scope, exclusions, roles, rules, UX, data history, and acceptance outcomes.
- Reject a material change that lacks a current approved Foundation or downstream artifact binding.

## Correctness

- Inspect validation, authorization, error handling, transactions, concurrency, migration, idempotency, recovery, and test intent where relevant.
- Check that tests prove the behavior rather than merely execute code.

## Quality

- Prefer simple, conventional, readable, maintainable designs.
- Flag duplication, hidden state, brittle effect timing, unjustified abstraction, dependency increase, insufficient observability, accessibility/localization regression, performance risk, and undocumented operational consequence.

## Independence

Do not change implementation. Return evidence-backed findings and required reruns to the orchestrator. Only the orchestrator may technically accept.
