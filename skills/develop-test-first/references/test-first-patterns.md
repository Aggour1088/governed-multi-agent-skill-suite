# Test-First Patterns

## Select the level

Use unit tests for deterministic rule logic, component tests for rendering and interaction, integration/contract tests for boundaries, end-to-end tests for critical journeys, and characterization tests for unexplained legacy behavior.

## Keep proof meaningful

Make the test fail for the intended missing or incorrect behavior. Avoid passing tests that only assert implementation details, mocks that bypass the boundary, random fixtures, or assertions too broad to identify a regression.

## Exceptions

Document why failing-first proof is impractical, unsafe, or disproportionate. Substitute a specific alternate proof. Do not let a documented exception remove independent QA or review.
