# Fresh-Context Adversarial Evaluations

This directory contains the ten adversarial scenarios required by the Feature Foundation. They are **fixtures**, not evidence that an evaluation has happened.

## How to run them

1. Use a fresh host context for each scenario; do not preload the desired answer.
2. Give the scenario's `prompt_fixture` to the named procedure or the orchestrator as appropriate.
3. Preserve the raw transcript, host/session metadata if the platform exposes it, timestamp, model/skill version, and all tool outputs.
4. Evaluate the result against `expected_safe_behavior`; do not award a pass for a plausible explanation that does not enforce the boundary.
5. Store a result artifact with a SHA-256 in a protected evidence system. Only then may the manifest status change from `not-run`.

## Interpretation

All critical scenarios must pass before describing a release as behaviorally evaluated. A structural validator, unit test, or checksum does not substitute for a fresh-context agent evaluation.

The raw standalone suite has no trusted host-attestation adapter, so it must not claim independent multi-agent evaluation based only on self-entered labels.
