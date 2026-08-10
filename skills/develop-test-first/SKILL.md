---
name: develop-test-first
description: Develop governed behavioral changes through a proportionate red-green-refactor cycle or legacy characterization tests. Use when implementing a bounded behavior change that needs executable proof before and after the minimum implementation; this is an engineering practice, not a substitute for independent QA.
---

# Develop Test First

## Direct invocation boundary

This procedure may modify a governed project only after the orchestrator supplies a validated assignment contract. If invoked directly without that contract, provide only a bounded read-only consultation, return control to `$orchestrate-owner-governed-delivery`, and do not modify a project, accept work, release, or communicate an owner decision. Do not call a direct or sequential pass independent unless a trusted host attests distinct principals; otherwise label it `separate-pass-not-independent`. This behavioral gate does not itself create host-level access control.

Use an executable behavior proof to drive implementation. Keep this procedure inside the implementer role; independent testing remains mandatory afterward.

During active governed delivery, work only under an implementation assignment. Do not call self-written tests independent QA, review, technical acceptance, or owner acceptance.

## Procedure

1. Restate one observable behavior, its invalid or boundary case, and the approved acceptance criterion.
2. Inspect existing test conventions and choose the narrowest meaningful level: unit, component, integration, contract, end-to-end, or characterization.
3. Write a test that fails for the intended reason before adding the minimum behavior. Record the failure output.
4. Implement only enough to make the behavior pass.
5. Refactor only while preserving passing behavior and rerun the relevant tests.
6. Add a regression, contract, property, or characterization test when the defect or legacy behavior demands it.
7. Use deterministic fixtures and avoid masking a broken behavior with broad mocks.
8. Record the test path, commands, red evidence, green evidence, residual risk, and implementation fingerprint.

## Exception rule

Use a documented exception only when a failing-first test is impractical or unsafe. Explain why, name the alternate proof, get it accepted in the assignment contract, and still require independent testing and review.

## Resources

- 'assets/test-first-evidence-template.md' — red-green-refactor record.
- 'references/test-first-patterns.md' — level selection and legacy guidance.
