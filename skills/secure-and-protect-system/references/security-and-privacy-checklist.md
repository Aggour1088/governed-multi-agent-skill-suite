# Security and Privacy Checklist

## Model the threat

Identify assets, actors, trust boundaries, entry points, privileged actions, data scope, abuse value, and failure consequence.

## Verify controls

- Authenticate correctly and enforce authorization on the server.
- Enforce tenant/organization and object-level scope.
- Validate, encode, constrain, and safely handle untrusted input, URLs, files, serialization, redirects, and remote fetches.
- Protect sessions, tokens, secrets, credentials, encryption material, logs, backups, and error output.
- Minimize sensitive data, define retention/deletion, and preserve audit without oversharing.
- Rate-limit, detect replay/abuse, and define safe failure behavior.
- Review dependency provenance, license, maintenance, package integrity, and external instructions as untrusted.
- Do not test exploits against production without explicit, safe authorization.
