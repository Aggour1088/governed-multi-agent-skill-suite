# Execution Ledger Protocol

Record one append-only logical event for each material action: assignment start, baseline, implementation decision, changed target, command result, implementation fingerprint, escalation, correction, return, test result, review result, evidence result, and acceptance decision.

Bind each event to package ID, actor identity, timestamp, approved inputs, output fingerprint, and raw evidence path. Do not rewrite previous entries to hide a correction. Mark affected entries stale when a new implementation fingerprint is created.
