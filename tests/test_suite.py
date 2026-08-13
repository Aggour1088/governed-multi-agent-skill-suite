from __future__ import annotations

import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


def load_validator(repository: Path):
    validator_path = repository / "scripts" / "validate_suite.py"
    spec = importlib.util.spec_from_file_location("suite_validator", validator_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load validator from {validator_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_repository_installer(
    repository: Path,
    suite_dir: Path,
    project_root: Path,
    *,
    verify_installed: bool = False,
) -> subprocess.CompletedProcess[str]:
    command = [
        sys.executable,
        str(repository / "scripts" / "install_repo_skills.py"),
        "--suite-dir",
        str(suite_dir),
        "--project-root",
        str(project_root),
    ]
    if verify_installed:
        command.append("--verify-installed")
    return subprocess.run(command, capture_output=True, text=True, check=False)


def initialize_git_repository(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["git", "init", "--quiet", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise AssertionError(result.stdout + result.stderr)


class SuiteValidationTests(unittest.TestCase):
    def test_release_validates(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [sys.executable, "scripts/validate_suite.py"],
            cwd=repository,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS: 24 skills", result.stdout)

    def test_release_documentation_passes_policy_validation(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        validator = load_validator(repository)
        errors = validator.validate_release_documents(repository)
        self.assertEqual(errors, [], "\n".join(errors))

    def test_documentation_validator_rejects_a_time_sensitive_publication_claim(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        validator = load_validator(repository)

        with tempfile.TemporaryDirectory() as temp_dir:
            copy_root = Path(temp_dir) / "suite"
            shutil.copytree(repository, copy_root, ignore=shutil.ignore_patterns(".git", "__pycache__"))
            readme = copy_root / "README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8").replace(
                    "Install only from a published versioned tag or release archive, not from a mutable branch.",
                    "This source has not yet been published as a GitHub release.",
                    1,
                ),
                encoding="utf-8",
            )

            errors = validator.validate_release_documents(copy_root)

        self.assertTrue(any("time-sensitive publication claim" in error for error in errors), errors)

    def test_documentation_validator_rejects_an_internal_runtime_path(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        validator = load_validator(repository)

        with tempfile.TemporaryDirectory() as temp_dir:
            copy_root = Path(temp_dir) / "suite"
            shutil.copytree(repository, copy_root, ignore=shutil.ignore_patterns(".git", "__pycache__"))
            guide = copy_root / "INSTALL.md"
            guide.write_text(
                guide.read_text(encoding="utf-8") + "\nExample internal path: /root/.codex/skills\n",
                encoding="utf-8",
            )

            errors = validator.validate_release_documents(copy_root)

        self.assertTrue(any("internal runtime path" in error for error in errors), errors)

    def test_documentation_validator_rejects_an_unsupported_web_claim(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        validator = load_validator(repository)

        with tempfile.TemporaryDirectory() as temp_dir:
            copy_root = Path(temp_dir) / "suite"
            shutil.copytree(repository, copy_root, ignore=shutil.ignore_patterns(".git", "__pycache__"))
            guide = copy_root / "INSTALL.md"
            guide.write_text(
                guide.read_text(encoding="utf-8").replace(
                    "Use a separately packaged and permitted plugin. The raw folders in this repository are not a web-installation format.",
                    "Raw folders in this repository install directly on the web.",
                    1,
                ),
                encoding="utf-8",
            )

            errors = validator.validate_release_documents(copy_root)

        self.assertTrue(any("ChatGPT Work on the web" in error for error in errors), errors)

    def test_documentation_validator_rejects_a_broken_local_link(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        validator = load_validator(repository)

        with tempfile.TemporaryDirectory() as temp_dir:
            copy_root = Path(temp_dir) / "suite"
            shutil.copytree(repository, copy_root, ignore=shutil.ignore_patterns(".git", "__pycache__"))
            readme = copy_root / "README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8").replace("(INSTALL.md)", "(missing-install.md)", 1),
                encoding="utf-8",
            )

            errors = validator.validate_release_documents(copy_root)

        self.assertTrue(any("broken local Markdown link" in error for error in errors), errors)

    def test_repository_installer_creates_an_empty_directory_and_blocks_any_existing_entry(self) -> None:
        repository = Path(__file__).resolve().parents[1]

        cases = (
            ("absent", True),
            ("existing empty", True),
            ("physical entry", False),
            ("dangling symlink", False),
            ("destination file", False),
            ("destination symlink", False),
            ("agents directory symlink", False),
            ("not a Git repository", False),
            ("nested project directory", False),
        )
        for label, should_succeed in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp_dir:
                temp_root = Path(temp_dir)
                project_root = temp_root / "project"
                if label == "nested project directory":
                    initialize_git_repository(project_root)
                    project_root = project_root / "nested"
                    project_root.mkdir()
                elif label != "not a Git repository":
                    initialize_git_repository(project_root)
                else:
                    project_root.mkdir()
                destination = project_root / ".agents" / "skills"
                if label == "existing empty":
                    destination.mkdir(parents=True)
                elif label == "physical entry":
                    (destination / "different-folder").mkdir(parents=True)
                elif label == "dangling symlink":
                    destination.mkdir(parents=True)
                    (destination / "different-link").symlink_to(temp_root / "missing-target")
                elif label == "destination file":
                    destination.parent.mkdir(parents=True)
                    destination.write_text("not a directory", encoding="utf-8")
                elif label == "destination symlink":
                    target = temp_root / "symlink-target"
                    target.mkdir()
                    destination.parent.mkdir(parents=True)
                    destination.symlink_to(target, target_is_directory=True)
                elif label == "agents directory symlink":
                    outside = temp_root / "outside-agents"
                    outside.mkdir()
                    (project_root / ".agents").symlink_to(outside, target_is_directory=True)

                result = run_repository_installer(repository, repository, project_root)

                if should_succeed:
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertTrue(destination.is_dir(), result.stdout + result.stderr)
                    self.assertTrue(
                        (destination / "orchestrate-owner-governed-delivery" / "SKILL.md").is_file(),
                        result.stdout + result.stderr,
                    )
                else:
                    self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertFalse(
                        (destination / "orchestrate-owner-governed-delivery").exists(),
                        result.stdout + result.stderr,
                    )
                    if label in {"physical entry", "dangling symlink"}:
                        self.assertIn("not empty", result.stdout.lower())
                    if label == "not a Git repository":
                        self.assertIn("git repository", result.stdout.lower())
                    if label == "nested project directory":
                        self.assertIn("repository root", result.stdout.lower())

    def test_repository_installer_copies_every_skill_file_and_detects_later_drift(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "project"
            initialize_git_repository(project_root)
            result = run_repository_installer(repository, repository, project_root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            source_root = repository / "skills"
            destination = project_root / ".agents" / "skills"
            source_files = sorted(
                path.relative_to(source_root) for path in source_root.rglob("*") if path.is_file()
            )
            destination_files = sorted(
                path.relative_to(destination) for path in destination.rglob("*") if path.is_file()
            )
            self.assertEqual(destination_files, source_files)
            for relative_path in source_files:
                self.assertEqual(
                    (destination / relative_path).read_bytes(),
                    (source_root / relative_path).read_bytes(),
                    relative_path.as_posix(),
                )

            changed_skill = destination / "orchestrate-owner-governed-delivery" / "SKILL.md"
            changed_skill.write_text("changed after installation\n", encoding="utf-8")
            verification = run_repository_installer(
                repository,
                repository,
                project_root,
                verify_installed=True,
            )
            self.assertNotEqual(verification.returncode, 0, verification.stdout + verification.stderr)
            self.assertIn("does not exactly match", verification.stdout.lower())

    def test_repository_installer_refuses_a_tampered_source_before_creating_a_destination(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            suite_copy = temp_root / "suite-copy"
            shutil.copytree(repository, suite_copy, ignore=shutil.ignore_patterns(".git", "__pycache__"))
            skill = suite_copy / "skills" / "orchestrate-owner-governed-delivery" / "SKILL.md"
            skill.write_text(skill.read_text(encoding="utf-8") + "\nTampered.\n", encoding="utf-8")
            project_root = temp_root / "project"
            initialize_git_repository(project_root)

            result = run_repository_installer(repository, suite_copy, project_root)

            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("source suite validation failed", result.stdout.lower())
            self.assertFalse((project_root / ".agents" / "skills").exists())


if __name__ == "__main__":
    unittest.main()
