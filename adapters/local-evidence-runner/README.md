# Local Evidence Runner Adapter

This adapter runs only an exact command that an active v2 work-package contract lists. It stores a redacted output artifact and hash-bound receipt outside the project workspace.

- Without `--host-controlled`, it emits **E1 (Reproducible)** evidence.
- With `--host-controlled`, a host injects an HMAC key that the agent cannot read and protects the evidence store. The receipt is marked **E2 (Host observed)** only under those external conditions.

The adapter does not prove agent identity, independent review, human understanding, production safety, or that a weak test is meaningful. Do not place the HMAC key in a project file, prompt, log, or agent-controlled environment.

Run `run_governed_command.py` with a current contract, project root, external evidence store, and allowed command ID. Verify signed receipts with `verify_receipt.py` using the same host-injected key.
