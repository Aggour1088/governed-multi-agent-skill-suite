# Install the Governed Multi-Agent Skill Suite

This repository contains **20 standalone skill folders**. Install each folder as a separate skill; do not treat the repository root as one skill.

## Who this guide is for

Use this guide only if you are a technical user, or an authorized AI agent, with all of the following:

- permission to read the release checkout and write to the target Git repository;
- Git and Python 3 in a POSIX-compatible environment (Linux, macOS, or WSL);
- Codex CLI or the Codex IDE extension available for the target project; and
- enough familiarity to stop and preserve the error output if a command fails.

This is not a one-click setup guide for ordinary ChatGPT web users. Native Windows is not supported for the full integrity verification in this release because its descriptor-safe validators require POSIX file APIs. Use WSL, Linux, or macOS for the supported route.

If an AI agent follows this guide, it must still have the project owner's authorization to modify the target repository. This guide does not grant permissions, install credentials, or authorize an overwrite.

## What installation route is correct?

OpenAI documents standalone skills for the ChatGPT desktop app, Codex CLI, and the Codex IDE extension. It documents repository-scoped discovery through `.agents/skills`, and separately documents a user scope at `$HOME/.agents/skills`. Feature availability varies by plan, platform, and workspace or machine administrator controls. See the current [official Build skills documentation](https://learn.chatgpt.com/docs/build-skills).

| Where you want to use the suite | Correct route |
| --- | --- |
| A Codex CLI or Codex IDE project that you control | Use the supported repository-scoped route below. It is the only route this guide automates and verifies. |
| A local user-wide scope | `$HOME/.agents/skills` is a documented scope, but this guide does not merge or overwrite user-wide skills. Use your host's normal skill-management process and review name collisions first. |
| ChatGPT desktop app | Standalone skills may be available in the Skills experience, subject to account and administrator controls. This repository does not provide an automatic desktop import. |
| ChatGPT Work on the web | Use a separately packaged and permitted plugin. The raw folders in this repository are not a web-installation format. |

## Before you install

1. Obtain a **published versioned tag or release archive**. Do not install a mutable `main` branch for production or sensitive work.
2. Clone that tag or extract that archive into a separate directory. Replace the placeholder only with a published release tag:

   ```bash
   git clone --branch <published-release-tag> --depth 1 https://github.com/Aggour1088/governed-multi-agent-skill-suite.git
   cd governed-multi-agent-skill-suite
   ```

3. Verify the untouched source checkout before it can write to any project:

   ```bash
   python3 scripts/release_checksums.py
   python3 scripts/validate_suite.py
   python3 scripts/validate_evaluation_suite.py
   python3 -m unittest discover -s tests -p 'test_*.py' -v
   ```

   Do **not** run `python3 scripts/release_checksums.py --write` as an installer. `--write` replaces the inventory and is only for a release maintainer deliberately preparing a new tag.

4. Treat a passing checksum inventory as a drift check, not an identity guarantee. It can show that the checkout matches its checked-in inventory; it cannot prove who created a GitHub tag, who supplied the archive, or that a command execution was independently attested. See [Release Integrity](docs/RELEASE_INTEGRITY.md).

## Supported route — install into one empty repository skill scope

Use this route only when the target is a Git repository that you control and its `.agents/skills` directory is absent or empty. The installer refuses a non-empty directory, a symlink, a nested project path, a source validation failure, and a copied tree that does not exactly match the verified source.

Set the two paths, then run the command as one unit:

```bash
SUITE_DIR="/absolute/path/to/governed-multi-agent-skill-suite"
PROJECT_ROOT="/absolute/path/to/your-git-repository"

python3 "$SUITE_DIR/scripts/install_repo_skills.py" \
  --suite-dir "$SUITE_DIR" \
  --project-root "$PROJECT_ROOT"
```

The command validates the source again before writing, copies through a temporary directory, verifies every installed file against the source, then places the 20 folders in:

```text
<PROJECT_ROOT>/.agents/skills/
```

It does not merge, overwrite, remove, update, or copy into a pre-existing skill collection. Do not overwrite an existing skill directory by hand. If it stops, do not rerun it over a partial result; inspect the output and destination first.

To re-check a completed copy without writing anything:

```bash
python3 "$SUITE_DIR/scripts/install_repo_skills.py" \
  --suite-dir "$SUITE_DIR" \
  --project-root "$PROJECT_ROOT" \
  --verify-installed
```

## Verify Codex discovery

Start Codex from the target repository root and use `/skills` in Codex CLI or the IDE extension. Confirm that all 20 skills appear, including `orchestrate-owner-governed-delivery`.

Then use an explicit, harmless request:

```text
$orchestrate-owner-governed-delivery Explain the owner-governed workflow without modifying this project.
```

Expected result: it should discuss the owner outcome, lifecycle, evidence, and limitations before proposing any project change. The installer proves an exact file copy; it does not itself prove that a particular Codex host has enabled local skills or has discovered them. If the skills do not appear, keep the installer output, check that Codex was started from `PROJECT_ROOT`, and consult your host or administrator controls before changing files.

## Updating safely

Do not copy a newer release over the installed folders.

1. Obtain and verify the newer versioned release in a separate directory.
2. Compare its skills against the current scope and decide deliberately whether an update is authorized.
3. Use a controlled update process that preserves a recovery copy and checks for name collisions. This installer intentionally refuses to replace an existing collection.
4. Run `/skills` and the read-only verification request again after any approved update.

## What this guide does not do

- It does not install the whole repository as one skill.
- It does not install a plugin or make the suite available in ChatGPT Work on the web.
- It does not create permissions, authenticate users or agents, add credentials, or configure GitHub rules.
- It does not make testing or review independent merely because separate role names appear in a record.
- It does not bypass project ownership, approval, testing, or review controls.
