# V2 Capability Matrix

Capability declarations tell the owner what the current host can actually do. They are **not enforcement** by themselves, and missing capability must reduce the evidence claim rather than be hidden.

| Capability | Core source installation | Local Evidence Runner | Protected CI / deployment adapter |
| --- | --- | --- | --- |
| Skill routing | `explicit-only`; implicit trigger is best-effort | `explicit-only` | Depends on configured project adapter |
| Tool mediation | `advisory` | `wrapper` for exact allowlisted commands only | Can be `sandbox-policy` / protected workflow |
| Agent identity | `session-label` at most | `session-label` unless host adds identity | `host-principal` when CI supplies it |
| Workspace isolation | `worktree` when Git is available | Uses declared project workspace | Depends on CI runner/sandbox |
| Test evidence | `reproducible` | E1 local; E2 only with host-controlled key/store | Can provide CI-attested evidence |
| Browser verification | `manual` or unavailable | Not provided | Host automated only if configured |
| CI/CD integration | `reporting-only` | Not provided | protected artifact/deploy only if configured |
| Secret boundary | `environment-scoped` by convention | HMAC key must be host-injected | short-lived protected credentials where configured |
| Production control | none in raw skills | none | CI-protected only if platform rules enforce it |

## Owner summary examples

- Core source only: “This installation can guide and record reproducible work, but it cannot prove independent agents, test execution, or protected deployment.”
- Local signed runner: “This installation can verify a receipt signature; the receipt is E2 only when the host, not the agent, protects its key and evidence store.”
- Protected CI adapter: “This installation can attest the configured CI job and artifact, but must still state whether browser checks, separate identities, and deployment protection are configured.”

## Compatibility discipline

For every published package, state the source version, adapter version, target host/version, capability profile, behavior-evaluation status, known restriction, and rollback path. Never tell users to install `latest` when an immutable versioned release is available.
