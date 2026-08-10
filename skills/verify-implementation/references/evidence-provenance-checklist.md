# Evidence Provenance Checklist

- Bind every report to work-package ID, approved input fingerprints, exact implementation fingerprint, actor identity, timestamp, environment, and raw evidence.
- Require different implementer, tester, and reviewer identities.
- Confirm `separate-pass-not-independent` unless a trusted host attestation is independently verified. A self-entered identity string is not proof of independence.
- Reject missing, failed, conditional-without-owner, stale, contradictory, or unauditable required evidence.
- Mark all affected evidence stale after a material code, configuration, test, requirement, data, environment, or decision change.
- Map approved requirements to appropriate current proof.
- Do not treat an agent statement, screenshot, happy-path mock, build, or local server as complete proof on its own.
