from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch


REPOSITORY = Path(__file__).resolve().parents[1]
EVIDENCE_VALIDATORS = (
    "skills/orchestrate-owner-governed-delivery/scripts/validate_work_package.py",
    "skills/verify-implementation/scripts/verify_evidence_record.py",
)


def load_module(relative_path: str, module_name: str):
    path = REPOSITORY / relative_path
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


class EvidenceIntegrityTests(unittest.TestCase):
    def make_record(self, validator, root: Path, now: datetime) -> dict:
        source = root / "src" / "service.py"
        source.parent.mkdir(parents=True)
        source.write_text("def calculate():\n    return 42\n", encoding="utf-8")

        foundation = root / ".governance" / "foundation.md"
        foundation.parent.mkdir(parents=True)
        foundation.write_text("approved foundation\n", encoding="utf-8")

        test_log = root / "evidence" / "test.log"
        review_log = root / "evidence" / "review.log"
        test_log.parent.mkdir(parents=True)
        test_log.write_text("python -m unittest: exit 0\n", encoding="utf-8")
        review_log.write_text("review: no blocking findings\n", encoding="utf-8")

        implementation = validator.compute_implementation_fingerprint(root, ["src/service.py"])
        timestamp = now.isoformat().replace("+00:00", "Z")
        return {
            "schema_version": "2.0",
            "work_package_id": "suite-hardening-001",
            "risk_track": "Standard",
            "owned_targets": ["src/service.py"],
            "roles": {
                "implementer_id": "implementer-principal",
                "tester_id": "tester-principal",
                "reviewer_id": "reviewer-principal",
                "specialist_verifier_ids": [],
            },
            "independence_status": "separate-pass-not-independent",
            "implementation_fingerprint": implementation,
            "approved_artifacts": [
                {
                    "id": "foundation",
                    "path": ".governance/foundation.md",
                    "sha256": sha256_file(foundation),
                }
            ],
            "checks": [
                {
                    "kind": "independent-test",
                    "status": "declared-passed",
                    "executor_role": "tester",
                    "declared_principal_id": "tester-principal",
                    "implementation_fingerprint": implementation,
                    "command": ["python3", "-m", "unittest"],
                    "exit_code": 0,
                    "evidence_artifacts": [{"path": "evidence/test.log", "sha256": sha256_file(test_log)}],
                    "recorded_at": timestamp,
                },
                {
                    "kind": "independent-review",
                    "status": "declared-passed",
                    "executor_role": "reviewer",
                    "declared_principal_id": "reviewer-principal",
                    "implementation_fingerprint": implementation,
                    "command": ["review-tool", "--diff"],
                    "exit_code": 0,
                    "evidence_artifacts": [{"path": "evidence/review.log", "sha256": sha256_file(review_log)}],
                    "recorded_at": timestamp,
                },
            ],
        }

    def test_validators_reject_self_declared_or_tampered_proof(self) -> None:
        now = utc_now()
        for index, relative_path in enumerate(EVIDENCE_VALIDATORS):
            with self.subTest(validator=relative_path), tempfile.TemporaryDirectory() as temp_dir:
                validator = load_module(relative_path, f"evidence_validator_{index}")
                root = Path(temp_dir)
                record = self.make_record(validator, root, now)

                self.assertEqual(
                    validator.validate_integrity(record, project_root=root, now=now),
                    [],
                    "The structural integrity lint should accept complete contained evidence.",
                )
                errors = validator.validate(record, project_root=root, now=now)
                self.assertTrue(
                    any("command execution" in error.lower() for error in errors),
                    "A standalone validator must never accept a self-declared completed record as proof.",
                )
                claimed_pass = self.make_record(validator, root / "claimed-pass", now)
                claimed_pass["checks"][0]["status"] = "passed"
                errors = validator.validate_integrity(claimed_pass, project_root=root / "claimed-pass", now=now)
                self.assertTrue(any("cannot claim a verified pass" in error.lower() for error in errors), errors)
                peer_helper = REPOSITORY / EVIDENCE_VALIDATORS[1 - index].replace("validate_work_package.py", "evidence_integrity.py").replace("verify_evidence_record.py", "evidence_integrity.py")
                own_helper = REPOSITORY / relative_path.replace("validate_work_package.py", "evidence_integrity.py").replace("verify_evidence_record.py", "evidence_integrity.py")
                self.assertEqual(own_helper.read_bytes(), peer_helper.read_bytes(), "Standalone integrity helpers must not drift.")

                tampered_hash = self.make_record(validator, root / "tampered-hash", now)
                tampered_hash["checks"][0]["evidence_artifacts"][0]["sha256"] = "sha256:" + "0" * 64
                errors = validator.validate(tampered_hash, project_root=root / "tampered-hash", now=now)
                self.assertTrue(any("hash" in error.lower() for error in errors), errors)

                bare_text = self.make_record(validator, root / "bare-text", now)
                bare_text["checks"][0].pop("evidence_artifacts")
                bare_text["checks"][0]["raw_evidence"] = ["unverified text"]
                errors = validator.validate(bare_text, project_root=root / "bare-text", now=now)
                self.assertTrue(any("evidence_artifacts" in error for error in errors), errors)

                invalid_time = self.make_record(validator, root / "invalid-time", now)
                invalid_time["checks"][0]["recorded_at"] = "not-a-timestamp"
                errors = validator.validate(invalid_time, project_root=root / "invalid-time", now=now)
                self.assertTrue(any("timestamp" in error.lower() for error in errors), errors)

                stale_fingerprint = self.make_record(validator, root / "stale-fingerprint", now)
                stale_fingerprint["implementation_fingerprint"] = "sha256:" + "f" * 64
                for check in stale_fingerprint["checks"]:
                    check["implementation_fingerprint"] = stale_fingerprint["implementation_fingerprint"]
                errors = validator.validate(stale_fingerprint, project_root=root / "stale-fingerprint", now=now)
                self.assertTrue(any("fingerprint" in error.lower() for error in errors), errors)

                false_independence = self.make_record(validator, root / "false-independence", now)
                false_independence["independence_status"] = "host-attested-independent"
                errors = validator.validate(false_independence, project_root=root / "false-independence", now=now)
                self.assertTrue(any("attestation" in error.lower() for error in errors), errors)

                overlapping_roles = self.make_record(validator, root / "overlapping-roles", now)
                overlapping_roles["roles"]["reviewer_id"] = "implementer-principal"
                errors = validator.validate(overlapping_roles, project_root=root / "overlapping-roles", now=now)
                self.assertTrue(any("distinct" in error.lower() for error in errors), errors)

                enhanced = self.make_record(validator, root / "enhanced", now)
                enhanced["risk_track"] = "Enhanced"
                errors = validator.validate(enhanced, project_root=root / "enhanced", now=now)
                self.assertTrue(any("Enhanced" in error for error in errors), errors)

    def test_validators_reject_a_path_swap_before_hashing(self) -> None:
        """A validator must retain an already-open internal evidence descriptor."""
        now = utc_now()
        for index, relative_path in enumerate(EVIDENCE_VALIDATORS):
            with self.subTest(validator=relative_path), tempfile.TemporaryDirectory() as temp_dir:
                validator = load_module(relative_path, f"evidence_race_validator_{index}")
                root = Path(temp_dir) / "project"
                record = self.make_record(validator, root, now)
                target = root / "evidence" / "test.log"
                outside = Path(temp_dir) / "outside.log"
                outside.write_text("external content\n", encoding="utf-8")
                record["checks"][0]["evidence_artifacts"][0]["sha256"] = sha256_file(outside)
                evidence_globals = validator.validate_evidence_artifacts.__globals__
                original_containment = evidence_globals["contained_regular_file"]
                swapped = False

                def swap_parent_after_containment(*args, **kwargs):
                    nonlocal swapped
                    result = original_containment(*args, **kwargs)
                    if args[1] == "evidence/test.log":
                        target.parent.rename(root / "evidence-internal")
                        target.parent.symlink_to(outside.parent, target_is_directory=True)
                        swapped = True
                    return result

                with patch.dict(evidence_globals, {"contained_regular_file": swap_parent_after_containment}):
                    errors = validator.validate_integrity(record, project_root=root, now=now)

                self.assertTrue(swapped, "The test must swap the evidence parent after it is opened.")
                self.assertTrue(
                    any(word in error.lower() for error in errors for word in ("hash", "symlink", "changed", "contained")),
                    errors,
                )

    def test_contained_hash_rejects_a_swap_at_the_descriptor_open(self) -> None:
        """The safe helper must bind the inode before it reads a checked artifact."""
        for index, relative_path in enumerate(EVIDENCE_VALIDATORS):
            with self.subTest(validator=relative_path), tempfile.TemporaryDirectory() as temp_dir:
                helper_path = relative_path.replace("validate_work_package.py", "evidence_integrity.py").replace(
                    "verify_evidence_record.py", "evidence_integrity.py"
                )
                helper = load_module(helper_path, f"descriptor_integrity_helper_{index}")
                root = Path(temp_dir) / "project"
                target = root / "evidence" / "test.log"
                target.parent.mkdir(parents=True)
                target.write_text("internal content\n", encoding="utf-8")
                outside = Path(temp_dir) / "outside.log"
                outside.write_text("external content\n", encoding="utf-8")
                expected = sha256_file(target)
                original_open = helper.os.open
                swapped = False

                def swap_before_descriptor_open(path, flags, *args, **kwargs):
                    nonlocal swapped
                    if path == "test.log" and "dir_fd" in kwargs:
                        target.unlink()
                        target.symlink_to(outside)
                        swapped = True
                    return original_open(path, flags, *args, **kwargs)

                with patch.object(helper.os, "open", new=swap_before_descriptor_open):
                    errors = helper.validate_artifact_reference(
                        root,
                        {"path": "evidence/test.log", "sha256": expected},
                        "test evidence",
                    )

                self.assertTrue(swapped, "The test must trigger the final-component swap.")
                self.assertTrue(any(word in error.lower() for error in errors for word in ("safely", "changed", "symlink")), errors)

    def test_contained_hash_rejects_a_parent_directory_swap(self) -> None:
        """A checked child path must not be reopened through a swapped parent symlink."""
        for index, relative_path in enumerate(EVIDENCE_VALIDATORS):
            with self.subTest(validator=relative_path), tempfile.TemporaryDirectory() as temp_dir:
                helper_path = relative_path.replace("validate_work_package.py", "evidence_integrity.py").replace(
                    "verify_evidence_record.py", "evidence_integrity.py"
                )
                helper = load_module(helper_path, f"parent_swap_integrity_helper_{index}")
                root = Path(temp_dir) / "project"
                target = root / "evidence" / "test.log"
                target.parent.mkdir(parents=True)
                target.write_text("internal content\n", encoding="utf-8")
                outside_dir = Path(temp_dir) / "outside"
                outside_dir.mkdir()
                outside = outside_dir / "test.log"
                outside.write_text("external content\n", encoding="utf-8")
                original_containment = helper.contained_regular_file

                def swap_parent_after_containment(*args, **kwargs):
                    result = original_containment(*args, **kwargs)
                    target.parent.rename(root / "evidence-internal")
                    target.parent.symlink_to(outside_dir, target_is_directory=True)
                    return result

                with patch.object(helper, "contained_regular_file", new=swap_parent_after_containment):
                    errors = helper.validate_artifact_reference(
                        root,
                        {"path": "evidence/test.log", "sha256": sha256_file(outside)},
                        "test evidence",
                    )

                self.assertTrue(
                    any(word in error.lower() for error in errors for word in ("safely", "changed", "symlink", "contained", "hash")),
                    errors,
                )

    def test_contained_hash_rejects_a_fifo_without_blocking(self) -> None:
        """An evidence path must fail closed instead of blocking on a FIFO."""
        if not hasattr(os, "mkfifo"):
            self.skipTest("FIFO fixtures are unavailable on this platform")
        for index, relative_path in enumerate(EVIDENCE_VALIDATORS):
            with self.subTest(validator=relative_path), tempfile.TemporaryDirectory() as temp_dir:
                helper_path = relative_path.replace("validate_work_package.py", "evidence_integrity.py").replace(
                    "verify_evidence_record.py", "evidence_integrity.py"
                )
                root = Path(temp_dir) / "project"
                fifo = root / "evidence" / "test.log"
                fifo.parent.mkdir(parents=True)
                os.mkfifo(fifo)
                code = "\n".join(
                    (
                        "import importlib.util",
                        "from pathlib import Path",
                        f"spec = importlib.util.spec_from_file_location('fifo_helper', {str(REPOSITORY / helper_path)!r})",
                        "module = importlib.util.module_from_spec(spec)",
                        "spec.loader.exec_module(module)",
                        f"root = Path({str(root)!r})",
                        "print(module.validate_artifact_reference(root, {'path': 'evidence/test.log', 'sha256': 'sha256:' + '0' * 64}, 'fifo evidence'))",
                    )
                )
                try:
                    result = subprocess.run(
                        [sys.executable, "-c", code],
                        text=True,
                        capture_output=True,
                        check=False,
                        timeout=2,
                    )
                except subprocess.TimeoutExpired as exc:
                    self.fail(f"FIFO handling blocked instead of failing closed: {exc}")

                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("not a regular file", result.stdout)

    def test_integrity_only_cli_reports_its_non_acceptance_boundary(self) -> None:
        now = utc_now()
        for index, relative_path in enumerate(EVIDENCE_VALIDATORS):
            with self.subTest(validator=relative_path), tempfile.TemporaryDirectory() as temp_dir:
                validator = load_module(relative_path, f"cli_evidence_validator_{index}")
                root = Path(temp_dir) / "project"
                record = self.make_record(validator, root, now)
                record_path = root / "evidence-record.json"
                record_path.write_text(json.dumps(record), encoding="utf-8")
                command = [
                    sys.executable,
                    str(REPOSITORY / relative_path),
                    str(record_path),
                    "--project-root",
                    str(root),
                ]

                integrity_only = subprocess.run(
                    [*command, "--integrity-only"],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                default = subprocess.run(command, text=True, capture_output=True, check=False)

                self.assertEqual(integrity_only.returncode, 0, integrity_only.stdout + integrity_only.stderr)
                self.assertIn("INTEGRITY_ONLY", integrity_only.stdout)
                self.assertIn("command execution remains unverified", integrity_only.stdout)
                self.assertNotEqual(default.returncode, 0, default.stdout + default.stderr)
                self.assertIn("command execution", default.stdout)


class ArtifactBindingTests(unittest.TestCase):
    def test_artifact_reader_keeps_the_checked_parent_directory_bound(self) -> None:
        """Artifact reads must not escape through a parent symlink swapped after containment."""
        validator = load_module(
            "skills/guard-approved-artifacts/scripts/check_approved_artifacts.py",
            "artifact_parent_swap_gate",
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            target = root / "governance" / "foundation.md"
            target.parent.mkdir(parents=True)
            target.write_text("internal foundation\n", encoding="utf-8")
            outside_dir = Path(temp_dir) / "outside"
            outside_dir.mkdir()
            outside = outside_dir / "foundation.md"
            outside.write_text("external foundation\n", encoding="utf-8")
            original_containment = validator.safe_regular_file

            def swap_parent_after_containment(*args, **kwargs):
                result = original_containment(*args, **kwargs)
                target.parent.rename(root / "governance-internal")
                target.parent.symlink_to(outside_dir, target_is_directory=True)
                return result

            with patch.object(validator, "safe_regular_file", new=swap_parent_after_containment):
                content, digest, relative = validator.read_contained_text_and_hash(
                    root,
                    "governance/foundation.md",
                    "Foundation",
                )

            self.assertEqual(relative, "governance/foundation.md")
            self.assertEqual(content, "internal foundation\n")
            self.assertEqual(digest, sha256_file(root / "governance-internal" / "foundation.md"))

    def test_artifact_reader_rejects_a_fifo_without_blocking(self) -> None:
        """A malicious artifact FIFO must be rejected without waiting for a writer."""
        if not hasattr(os, "mkfifo"):
            self.skipTest("FIFO fixtures are unavailable on this platform")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            fifo = root / "governance" / "foundation.md"
            fifo.parent.mkdir(parents=True)
            os.mkfifo(fifo)
            script = REPOSITORY / "skills/guard-approved-artifacts/scripts/check_approved_artifacts.py"
            code = "\n".join(
                (
                    "import importlib.util",
                    "from pathlib import Path",
                    f"spec = importlib.util.spec_from_file_location('artifact_fifo_helper', {str(script)!r})",
                    "module = importlib.util.module_from_spec(spec)",
                    "spec.loader.exec_module(module)",
                    f"root = Path({str(root)!r})",
                    "try:",
                    "    module.read_contained_text_and_hash(root, 'governance/foundation.md', 'Foundation')",
                    "except ValueError as exc:",
                    "    print(str(exc))",
                    "else:",
                    "    print('unexpected pass')",
                )
            )
            try:
                result = subprocess.run(
                    [sys.executable, "-c", code],
                    text=True,
                    capture_output=True,
                    check=False,
                    timeout=2,
                )
            except subprocess.TimeoutExpired as exc:
                self.fail(f"FIFO handling blocked instead of failing closed: {exc}")

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("not a regular file", result.stdout)

    def test_artifact_gate_requires_canonical_frontmatter_binding(self) -> None:
        validator = load_module(
            "skills/guard-approved-artifacts/scripts/check_approved_artifacts.py",
            "artifact_gate",
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            foundation = root / ".governance" / "features" / "alpha" / "foundation.md"
            foundation.parent.mkdir(parents=True)
            approval = "sha256:" + "a" * 64
            foundation.write_text(
                "---\nstatus: APPROVED_FOR_SPECIFICATION\napproval_fingerprint: " + approval + "\n---\nApproved scope.\n",
                encoding="utf-8",
            )
            foundation_hash = sha256_file(foundation)
            artifact = root / ".governance" / "features" / "alpha" / "specification.md"
            artifact.write_text(
                "---\n"
                "artifact_type: specification\n"
                "foundation_path: .governance/features/alpha/foundation.md\n"
                f"foundation_content_sha256: {foundation_hash}\n"
                f"foundation_approval_fingerprint: {approval}\n"
                "---\nA specification.\n",
                encoding="utf-8",
            )

            self.assertEqual(validator.validate(root, foundation, [artifact]), [])

            prose_only = root / ".governance" / "features" / "alpha" / "prose-only.md"
            prose_only.write_text(f"Here is the approved fingerprint: {approval}\n", encoding="utf-8")
            errors = validator.validate(root, foundation, [prose_only])
            self.assertTrue(any("frontmatter" in error.lower() or "binding" in error.lower() for error in errors), errors)

            foundation.write_text(foundation.read_text(encoding="utf-8") + "Changed after approval.\n", encoding="utf-8")
            errors = validator.validate(root, foundation, [artifact])
            self.assertTrue(any("content hash" in error.lower() for error in errors), errors)


class AdapterWriteSafetyTests(unittest.TestCase):
    def test_adapter_apply_refuses_symlinked_target_without_touching_external_file(self) -> None:
        script = REPOSITORY / "skills/init-owner-governance/scripts/sync_governance_adapters.py"
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            policy = root / ".governance" / "owner-governed-delivery.md"
            policy.parent.mkdir(parents=True)
            policy.write_text("policy\n", encoding="utf-8")
            outside = Path(temp_dir) / "outside.md"
            outside.write_text("do not alter\n", encoding="utf-8")
            (root / "AGENTS.md").symlink_to(outside)

            result = subprocess.run(
                [sys.executable, str(script), str(root), "--apply", "--host", "codex"],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(outside.read_text(encoding="utf-8"), "do not alter\n")

    def test_adapter_apply_refuses_a_symlinked_parent_directory(self) -> None:
        script = REPOSITORY / "skills/init-owner-governance/scripts/sync_governance_adapters.py"
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            policy = root / ".governance" / "owner-governed-delivery.md"
            policy.parent.mkdir(parents=True)
            policy.write_text("policy\n", encoding="utf-8")
            outside = Path(temp_dir) / "outside"
            outside.mkdir()
            (root / ".github").symlink_to(outside, target_is_directory=True)

            result = subprocess.run(
                [sys.executable, str(script), str(root), "--apply", "--host", "copilot"],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse((outside / "copilot-instructions.md").exists())

    def test_adapter_apply_writes_a_regular_contained_file(self) -> None:
        script = REPOSITORY / "skills/init-owner-governance/scripts/sync_governance_adapters.py"
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            policy = root / ".governance" / "owner-governed-delivery.md"
            policy.parent.mkdir(parents=True)
            policy.write_text("policy\n", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(script), str(root), "--apply", "--host", "codex"],
                text=True,
                capture_output=True,
                check=False,
            )

            target = root / "AGENTS.md"
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(target.is_file())
            self.assertFalse(target.is_symlink())
            self.assertIn("OWNER-GOVERNED DELIVERY: BEGIN", target.read_text(encoding="utf-8"))

    def test_adapter_apply_rejects_an_end_marker_before_begin_without_mutating(self) -> None:
        script = REPOSITORY / "skills/init-owner-governance/scripts/sync_governance_adapters.py"
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            policy = root / ".governance" / "owner-governed-delivery.md"
            policy.parent.mkdir(parents=True)
            policy.write_text("policy\n", encoding="utf-8")
            target = root / "AGENTS.md"
            malformed = (
                "Before\n"
                "<!-- OWNER-GOVERNED DELIVERY: END -->\n"
                "Between\n"
                "<!-- OWNER-GOVERNED DELIVERY: BEGIN -->\n"
                "After\n"
            )
            target.write_text(malformed, encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(script), str(root), "--apply", "--host", "codex"],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("malformed governance markers", result.stdout)
            self.assertEqual(target.read_text(encoding="utf-8"), malformed)

    def test_adapter_apply_rejects_a_fifo_policy_without_blocking(self) -> None:
        """An untrusted policy FIFO must fail closed instead of hanging the adapter."""
        if not hasattr(os, "mkfifo"):
            self.skipTest("FIFO fixtures are unavailable on this platform")
        script = REPOSITORY / "skills/init-owner-governance/scripts/sync_governance_adapters.py"
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            policy = root / ".governance" / "owner-governed-delivery.md"
            policy.parent.mkdir(parents=True)
            os.mkfifo(policy)
            try:
                result = subprocess.run(
                    [sys.executable, str(script), str(root), "--apply", "--host", "codex"],
                    text=True,
                    capture_output=True,
                    check=False,
                    timeout=2,
                )
            except subprocess.TimeoutExpired as exc:
                self.fail(f"adapter blocked on a FIFO policy instead of failing closed: {exc}")

            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("non-regular file", result.stdout)


class DeliveryHardeningTests(unittest.TestCase):
    def test_all_specialists_have_a_direct_invocation_boundary(self) -> None:
        skills = sorted((REPOSITORY / "skills").iterdir())
        missing = []
        for skill in skills:
            if skill.name == "orchestrate-owner-governed-delivery" or not skill.is_dir():
                continue
            text = (skill / "SKILL.md").read_text(encoding="utf-8")
            if not all(
                phrase in text
                for phrase in (
                    "## Direct invocation boundary",
                    "assignment contract",
                    "read-only consultation",
                    "do not modify a project",
                )
            ):
                missing.append(skill.name)
        self.assertEqual(missing, [], f"Specialists missing their direct-invocation safety gate: {missing}")

    def test_suite_validator_rejects_mutable_actions_and_missing_specialist_gate(self) -> None:
        validator = load_module("scripts/validate_suite.py", "suite_validator_hardening")
        self.assertEqual(validator.validate_workflow_security(REPOSITORY), [])
        self.assertEqual(validator.validate_specialist_invocation_boundaries(REPOSITORY), [])
        workflow_text = (REPOSITORY / ".github" / "workflows" / "validate.yml").read_text(encoding="utf-8")
        for command in (
            "python scripts/validate_suite.py",
            "python scripts/release_checksums.py",
            "python scripts/validate_evaluation_suite.py",
            "python -m unittest discover -s tests -p 'test_*.py' -v",
            "python -m compileall -q scripts skills",
        ):
            self.assertIn(command, workflow_text)

        with tempfile.TemporaryDirectory() as temp_dir:
            copy_root = Path(temp_dir) / "suite"
            shutil.copytree(REPOSITORY, copy_root, ignore=shutil.ignore_patterns(".git", "__pycache__"))
            workflow = copy_root / ".github" / "workflows" / "validate.yml"
            workflow.write_text(
                workflow.read_text(encoding="utf-8")
                .replace("actions/checkout@", "actions/checkout@v4 # ", 1)
                .replace("      - run: python scripts/release_checksums.py\n", "", 1),
                encoding="utf-8",
            )
            skill = copy_root / "skills" / "engineer-backend-and-data" / "SKILL.md"
            skill.write_text(
                skill.read_text(encoding="utf-8").replace("## Direct invocation boundary", "## Invocation", 1),
                encoding="utf-8",
            )

            workflow_errors = validator.validate_workflow_security(copy_root)
            boundary_errors = validator.validate_specialist_invocation_boundaries(copy_root)

        self.assertTrue(any("immutable full SHA" in error for error in workflow_errors), workflow_errors)
        self.assertTrue(any("release_checksums" in error for error in workflow_errors), workflow_errors)
        self.assertTrue(any("direct-invocation" in error for error in boundary_errors), boundary_errors)

    def test_suite_validator_rejects_invalid_openai_yaml(self) -> None:
        validator = load_module("scripts/validate_suite.py", "suite_validator_openai_yaml")
        with tempfile.TemporaryDirectory() as temp_dir:
            copy_root = Path(temp_dir) / "suite"
            shutil.copytree(REPOSITORY, copy_root, ignore=shutil.ignore_patterns(".git", "__pycache__"))
            skill = copy_root / "skills" / "engineer-backend-and-data"
            ui_file = skill / "agents" / "openai.yaml"
            ui_file.write_text(
                "interface: [not a mapping\n"
                "policy:\n"
                "  allow_implicit_invocation: false\n"
                "  default_prompt: Use $engineer-backend-and-data.\n",
                encoding="utf-8",
            )

            errors = validator.validate_skill(skill)

        self.assertTrue(any("openai.yaml" in error and "YAML" in error for error in errors), errors)

    def test_suite_validator_rejects_duplicate_openai_yaml_products(self) -> None:
        validator = load_module("scripts/validate_suite.py", "suite_validator_openai_yaml_duplicates")
        with tempfile.TemporaryDirectory() as temp_dir:
            copy_root = Path(temp_dir) / "suite"
            shutil.copytree(REPOSITORY, copy_root, ignore=shutil.ignore_patterns(".git", "__pycache__"))
            skill = copy_root / "skills" / "engineer-backend-and-data"
            ui_file = skill / "agents" / "openai.yaml"
            ui_file.write_text(
                ui_file.read_text(encoding="utf-8").replace("    - CODEX\n", "    - CODEX\n    - CODEX\n"),
                encoding="utf-8",
            )

            errors = validator.validate_skill(skill)

        self.assertTrue(any("products must list" in error for error in errors), errors)

    def test_suite_validator_rejects_unsupported_openai_yaml_product_and_asset_path(self) -> None:
        validator = load_module("scripts/validate_suite.py", "suite_validator_openai_yaml_supported_fields")
        with tempfile.TemporaryDirectory() as temp_dir:
            copy_root = Path(temp_dir) / "suite"
            shutil.copytree(REPOSITORY, copy_root, ignore=shutil.ignore_patterns(".git", "__pycache__"))
            skill = copy_root / "skills" / "engineer-backend-and-data"
            ui_file = skill / "agents" / "openai.yaml"
            ui_file.write_text(
                ui_file.read_text(encoding="utf-8")
                .replace("    - CHAT\n", "    - chatgpt\n", 1)
                .replace("  icon_small: ./assets/icon.svg", "  icon_small: assets/icon.svg", 1),
                encoding="utf-8",
            )

            errors = validator.validate_skill(skill)

        self.assertTrue(any("unsupported product" in error for error in errors), errors)
        self.assertTrue(any("icon_small must start with ./" in error for error in errors), errors)

    def test_suite_validator_rejects_an_undersized_openai_svg_icon(self) -> None:
        validator = load_module("scripts/validate_suite.py", "suite_validator_openai_svg_icon")
        with tempfile.TemporaryDirectory() as temp_dir:
            copy_root = Path(temp_dir) / "suite"
            shutil.copytree(REPOSITORY, copy_root, ignore=shutil.ignore_patterns(".git", "__pycache__"))
            skill = copy_root / "skills" / "engineer-backend-and-data"
            icon = skill / "assets" / "icon.svg"
            icon.write_text(
                icon.read_text(encoding="utf-8").replace(
                    'width="48" height="48"', 'width="24" height="24"', 1
                ),
                encoding="utf-8",
            )

            errors = validator.validate_skill(skill)

        self.assertTrue(any("at least 48 by 48" in error for error in errors), errors)

    def test_release_checksums_detect_tampering_and_do_not_claim_a_missing_signature(self) -> None:
        validator = load_module("scripts/validate_suite.py", "suite_validator_release_integrity")
        self.assertEqual(validator.validate_release_checksums(REPOSITORY), [])
        integrity_guide = (REPOSITORY / "docs" / "RELEASE_INTEGRITY.md").read_text(encoding="utf-8").lower()
        self.assertIn("checksummed, not signed", integrity_guide)
        self.assertIn("owner's signing key", integrity_guide)

        with tempfile.TemporaryDirectory() as temp_dir:
            copy_root = Path(temp_dir) / "suite"
            shutil.copytree(REPOSITORY, copy_root, ignore=shutil.ignore_patterns(".git", "__pycache__"))
            readme = copy_root / "README.md"
            readme.write_text(readme.read_text(encoding="utf-8") + "\nTampered after checksums.\n", encoding="utf-8")
            errors = validator.validate_release_checksums(copy_root)

        self.assertTrue(any("checksum" in error.lower() for error in errors), errors)

    def test_release_checksums_reject_a_symlinked_release_file(self) -> None:
        validator = load_module("scripts/validate_suite.py", "suite_validator_release_symlink")
        with tempfile.TemporaryDirectory() as temp_dir:
            copy_root = Path(temp_dir) / "suite"
            shutil.copytree(REPOSITORY, copy_root, ignore=shutil.ignore_patterns(".git", "__pycache__"))
            external = Path(temp_dir) / "external.txt"
            external.write_text("external\n", encoding="utf-8")
            (copy_root / "docs" / "linked-release-file.txt").symlink_to(external)
            errors = validator.validate_release_checksums(copy_root)

        self.assertTrue(any("symlink" in error.lower() for error in errors), errors)

    def test_release_checksum_writer_refuses_a_symlinked_inventory(self) -> None:
        """Writing SHA256SUMS must never follow a symlink to an external file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            copy_root = Path(temp_dir) / "suite"
            shutil.copytree(REPOSITORY, copy_root, ignore=shutil.ignore_patterns(".git", "__pycache__"))
            external = Path(temp_dir) / "external-inventory.txt"
            external.write_text("do not overwrite\n", encoding="utf-8")
            checksum_file = copy_root / "SHA256SUMS"
            checksum_file.unlink()
            checksum_file.symlink_to(external)

            result = subprocess.run(
                [
                    sys.executable,
                    str(copy_root / "scripts" / "release_checksums.py"),
                    "--write",
                    "--release-maintainer",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(external.read_text(encoding="utf-8"), "do not overwrite\n")
            self.assertTrue(checksum_file.is_symlink())

    def test_release_checksum_writer_requires_explicit_maintainer_acknowledgment(self) -> None:
        """A consumer cannot accidentally replace the release inventory during verification."""
        with tempfile.TemporaryDirectory() as temp_dir:
            copy_root = Path(temp_dir) / "suite"
            shutil.copytree(REPOSITORY, copy_root, ignore=shutil.ignore_patterns(".git", "__pycache__"))
            inventory = copy_root / "SHA256SUMS"
            before = inventory.read_bytes()

            result = subprocess.run(
                [sys.executable, str(copy_root / "scripts" / "release_checksums.py"), "--write"],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("release-maintainer", result.stdout.lower())
            self.assertEqual(inventory.read_bytes(), before)

    def test_release_documentation_seals_checksums_before_tagging(self) -> None:
        validator = load_module("scripts/validate_suite.py", "suite_validator_release_order")
        self.assertEqual(validator.validate_release_documents(REPOSITORY), [])
        with tempfile.TemporaryDirectory() as temp_dir:
            copy_root = Path(temp_dir) / "suite"
            shutil.copytree(REPOSITORY, copy_root, ignore=shutil.ignore_patterns(".git", "__pycache__"))
            release_integrity = copy_root / "docs" / "RELEASE_INTEGRITY.md"
            release_integrity.write_text(
                release_integrity.read_text(encoding="utf-8").replace("before creating the tag", "after creating the tag", 1),
                encoding="utf-8",
            )
            errors = validator.validate_release_documents(copy_root)

        self.assertTrue(any("seal SHA256SUMS" in error for error in errors), errors)

    def test_installer_route_revalidates_source_and_refuses_overwrite(self) -> None:
        guide = (REPOSITORY / "INSTALL.md").read_text(encoding="utf-8")
        route = re.search(r"^## Supported route.*?(?=^## |\Z)", guide, flags=re.DOTALL | re.MULTILINE)
        self.assertIsNotNone(route)
        assert route is not None
        route_text = route.group(0)
        self.assertIn("scripts/install_repo_skills.py", route_text)
        self.assertIn("validates the source again before writing", route_text)
        self.assertIn("does not merge, overwrite", route_text)
        self.assertIn("temporary directory", route_text)
        self.assertIn("Do **not** run `python3 scripts/release_checksums.py --write`", guide)

    def test_security_policy_never_claims_self_declared_execution_is_verified(self) -> None:
        policy = (REPOSITORY / "SECURITY.md").read_text(encoding="utf-8").lower()
        self.assertIn("do not accept self-declared execution records", policy.replace("**", ""))
        self.assertNotIn("fail closed when a record uses self-declared evidence", policy)


class BehavioralEvaluationAssetTests(unittest.TestCase):
    def test_adversarial_evaluation_suite_is_present_and_does_not_fabricate_execution(self) -> None:
        validator = load_module("scripts/validate_evaluation_suite.py", "evaluation_validator")
        self.assertEqual(validator.validate(REPOSITORY), [])
        data = json.loads((REPOSITORY / "evaluations" / "adversarial-scenarios.json").read_text(encoding="utf-8"))
        self.assertEqual(data["evaluation_status"], "not-run")

        with tempfile.TemporaryDirectory() as temp_dir:
            copy_root = Path(temp_dir) / "suite"
            shutil.copytree(REPOSITORY, copy_root, ignore=shutil.ignore_patterns(".git", "__pycache__"))
            scenario_file = copy_root / "evaluations" / "adversarial-scenarios.json"
            data = json.loads(scenario_file.read_text(encoding="utf-8"))
            data["evaluation_status"] = "passed"
            scenario_file.write_text(json.dumps(data), encoding="utf-8")
            errors = validator.validate(copy_root)

        self.assertTrue(any("result artifact" in error.lower() for error in errors), errors)

    def test_evaluation_validator_rejects_a_fifo_scenario_without_blocking(self) -> None:
        """The standalone fixture validator must not block on a replaced scenario FIFO."""
        if not hasattr(os, "mkfifo"):
            self.skipTest("FIFO fixtures are unavailable on this platform")
        with tempfile.TemporaryDirectory() as temp_dir:
            copy_root = Path(temp_dir) / "suite"
            shutil.copytree(REPOSITORY, copy_root, ignore=shutil.ignore_patterns(".git", "__pycache__"))
            scenario_file = copy_root / "evaluations" / "adversarial-scenarios.json"
            scenario_file.unlink()
            os.mkfifo(scenario_file)
            try:
                result = subprocess.run(
                    [sys.executable, str(copy_root / "scripts" / "validate_evaluation_suite.py")],
                    text=True,
                    capture_output=True,
                    check=False,
                    timeout=2,
                )
            except subprocess.TimeoutExpired as exc:
                self.fail(f"evaluation validation blocked on a FIFO fixture: {exc}")

            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("cannot read adversarial evaluation fixtures", result.stdout)


if __name__ == "__main__":
    unittest.main()
