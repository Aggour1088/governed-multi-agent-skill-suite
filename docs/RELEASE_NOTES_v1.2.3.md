# v1.2.3 Publication-Status Correction

## What changed

- Removed time-sensitive statements from the README and export manifest that said the source was not yet published.
- Made the release boundary explicit: a matching GitHub versioned tag and Release page establish publication; source files do not assert publication status.
- Updated current-distribution references from v1.2.2 to v1.2.3 where they identify this release line.

## What this release does not claim

- It does not assert publication status inside the source tree. Check the repository's matching tag and Release page instead.
- It does not prove a live Codex host has discovered the installed skills; `/skills` in the target host remains the discovery check.
- It does not prove that two declared roles were separate agents or authenticate an identity, command execution, GitHub account, or release archive.
- It does not make the raw folders installable in ChatGPT Work on the web. A separately packaged and permitted plugin is required for that surface.

## Release use

Install only from the matching published versioned tag or release archive, not from `main`. Follow [Release Integrity](RELEASE_INTEGRITY.md) before creating a later version.
