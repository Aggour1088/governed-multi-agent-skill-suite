# Artifact Integrity Checklist

## Bind every downstream artifact

Require canonical frontmatter on each downstream artifact: `foundation_path`, `foundation_content_sha256`, and `foundation_approval_fingerprint`. The path must be contained under the project root; the content hash and approval fingerprint must match the current approved Foundation. Treat a fingerprint merely quoted in prose, a symlinked path, a mismatch, or a missing link as a blocker.

## Preserve the owner decision

Check problem, users, scope, exclusions, protected behavior, roles, rules, owner controls, historical behavior, risks, recovery, and acceptance outcomes. Return material change to the Foundation.

## Ensure execution readiness

Check specification clarity, architecture evidence, task ownership, no overlapping writes, role separation, baseline, test/review evidence, specialist impact, rollback, release, and owner milestones.

## Classify drift

Block Critical and High drift. A conditional pass must name the condition, owner, containment, deadline, and whether execution remains allowed.
