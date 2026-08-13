# v2.0.0 Behavior-Evaluation Record

## Result

The v2.0.0 router completed the full maintained adversarial catalogue: **18 passed, 0 failed, 0 partial, 0 not run**.

This statement applies only to the named configuration:

- configuration ID: chatgpt-codex-gpt-5-6-platform-managed;
- host: ChatGPT Codex Work Mode (platform-managed);
- model: GPT-5.6 Codex (platform-managed, reasoning platform-managed);
- evaluated on: 2026-08-13 UTC;
- evidence level: E1 reproducible.

The canonical generated result is the [raw scorecard](../../evaluations/results/codex-gpt-5-6-2026-08-13/scorecard.md). It binds every run to the exact prompt, transcript, normalized tool trace, capability profile, and these routed source fingerprints:

- router: sha256:af1363f146097dd650b246cb081f18e2deeed7d06fe4d28597a978d4c59a1780;
- routing policy: sha256:b3a03063f237ab08b585e652d32710cfe2f6536aba1d6cf373f4aa96e1c07ce3;
- source hierarchy policy: sha256:b1dbca3501f5195aa3b5d5104bb6e7bb100ccdb0650bfa6d8169ea796936cbac.

## Method

Each scenario used a newly spawned Codex context. The target was explicitly invoked through $using-governed-suite, received the exact user prompt only after reading the router and its two policy references, and was not given the scenario catalogue, expected safe behavior, other results, or a project task. No project, external, credential, deployment, or product mutation was requested.

The outcome is retained as E1 because the transcripts and tool traces are reproducible and hash-bound, but the host did not provide a protected audit receipt or independent-principal attestation.

## Remediation before the final run

Pre-final fresh-context probes exposed gaps in how directly the router rejected post-hoc testing, premature architecture selection, overly strong evidence labels, and several common shortcut requests. The router and its static validator were strengthened before the complete final rerun to require:

- red-first evidence or a documented pre-approved testing exception;
- workload model and service targets before scalability architecture endorsement;
- E2+ proof before a Verified label;
- explicit controls for dependencies, UI proof, causal fixes, requirement change control, unavailable checks, customer data, security exceptions, resumption, branch release, secrets, and independent-review claims.

The final scorecard is the release evidence. These remediation notes explain why the final rerun occurred; they do not convert earlier exploratory probes into a passing result.

## Boundary

Do not generalize this result to another host, model, configuration, router revision, or real project workflow. It does not prove host enforcement, independent review, production authorization, browser accessibility, or CI protection. Re-run the catalogue and retain new evidence when any of those conditions materially change.
