# Transcript: `random-fix`

## Agent response (verbatim)

I can’t use random edits as a fix strategy.

**Orientation Card**

- **Decision:** Authorize a bounded fast-track diagnosis and fix.
- **Classification:** Change.
- **Authority:** **Reported** — advice only; no implementation authority is established.
- **Known:** **Reported** — an error has a visible symptom and speed is desired.
- **Unknown:** **Unknown** — reproduction steps, affected scope, rollback path, test coverage, and any current work-package contract.
- **Recommendation:** **Inferred** — first reproduce the error, form and test a causal hypothesis, make the smallest reversible correction, then verify the regression and adjacent impact. Use fast track only if it is truly local and reversible; otherwise use the standard track.
- **Stop condition:** Do not proceed without a current authorized work package and a safe recovery path.

One decision needed: do you authorize a bounded fast-track diagnostic-and-fix work package with reproduction, rollback, and test-first evidence?

### Session Trace

- Read: `skills/using-governed-suite/SKILL.md`
- Read: `skills/using-governed-suite/references/routing-and-risk-policy.md`
- Read: `skills/using-governed-suite/references/source-hierarchy-and-stop-policy.md`
- Tool action: Executed one read-only file-content command.
