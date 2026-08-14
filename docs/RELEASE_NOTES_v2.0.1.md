# v2.0.1 — GitHub Rendering Compatibility Patch

This patch removes Mermaid rich-diagram blocks from the public README and Feature Foundation document. They are replaced with portable plain-text diagrams so GitHub remains readable when its Mermaid renderer is unavailable or fails.

## What changed

- Replaced the two GitHub-rendered Mermaid diagrams with equivalent plain-text workflow diagrams.
- Added a validation rule and regression test that reject Mermaid fences anywhere in the release documentation.
- Updated release identity and security-policy references to v2.0.1.

## What did not change

This patch does not change the skills, first-turn router, routing policy, installation path, evidence records, or the completed v2.0.0 behavior evaluation. The v2.0.0 E1 result remains limited to the named `chatgpt-codex-gpt-5-6-platform-managed` configuration and its recorded source fingerprints.

## Upgrade

Use the published v2.0.1 tag or release archive. Keep v2.0.0 available as a recovery copy if you need to compare the rendering-only patch.
