from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[1]


def load_module(relative_path: str, module_name: str):
    path = REPOSITORY / relative_path
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def initialize_git_repository(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    commands = (
        ["git", "init", "--quiet", str(path)],
        ["git", "-C", str(path), "config", "user.name", "Suite Test"],
        ["git", "-C", str(path), "config", "user.email", "suite-test@example.invalid"],
    )
    for command in commands:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)


def commit_all(path: Path, message: str = "baseline") -> str:
    for command in (
        ["git", "-C", str(path), "add", "."],
        ["git", "-C", str(path), "commit", "--quiet", "-m", message],
        ["git", "-C", str(path), "rev-parse", "HEAD"],
    ):
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)
    return result.stdout.strip()


def make_contract(now: datetime, *, risk_track: str = "Standard") -> dict:
    return {
        "schema_version": "2.0",
        "contract_id": "suite-owner-protection-001",
        "status": "active",
        "project": {"id": "sample-project", "baseline_revision": "a" * 40},
        "lifecycle_state": "PLAN",
        "risk_track": risk_track,
        "created_at": utc(now),
        "expires_at": utc(now + timedelta(hours=12)),
        "outcome": {
            "owner_visible_result": "A safe, documented change is prepared.",
            "acceptance_criteria": ["The focused behavior has current evidence."],
            "exclusions": ["No production deployment."],
            "non_goals": ["No unrelated refactor."],
            "success_metrics": ["The stated acceptance criterion is met."],
        },
        "approved_sources": [
            {
                "id": "foundation",
                "path": ".governance/foundation.md",
                "sha256": "sha256:" + "b" * 64,
            }
        ],
        "scope": {
            "owned_targets": ["src/service.py"],
            "interfaces": ["service.calculate"],
            "database_objects": [],
            "environments": ["test"],
            "parallel_write_groups": [],
        },
        "authority": {
            "mutation_allowed": True,
            "allowed_commands": [
                {
                    "id": "focused-test",
                    "argv": [sys.executable, "-m", "unittest"],
                    "cwd": ".",
                    "timeout_seconds": 120,
                }
            ],
            "dependency_changes": "forbidden",
            "production_action": "prohibited",
        },
        "roles": {
            "implementer_id": "implementer-session",
            "tester_id": "tester-session",
            "reviewer_id": "reviewer-session",
            "independence_claim": "not-attested",
        },
        "evidence": {
            "minimum_level": "E1",
            "freshness_hours": 24,
            "required_checks": ["independent-test", "independent-review"],
        },
        "operations": {
            "rollback_or_forward_recovery": "Revert the bounded change before release.",
            "stop_conditions": ["Scope or risk changes."],
            "observation_period": "not applicable before release",
        },
        "economics": {
            "model_tier": "standard",
            "reasoning_effort": "medium",
            "max_turns": 8,
            "max_cost": "owner-approved budget",
            "fix_circuit_breaker": 2,
        },
        "capability_profile": {
            "skill_routing": "explicit-only",
            "tool_mediation": "advisory",
            "agent_identity": "session-label",
            "workspace_isolation": "worktree",
            "test_evidence": "reproducible",
            "browser_verification": "manual",
            "ci_cd_integration": "reporting-only",
            "secret_boundary": "environment-scoped",
            "production_control": "owner-confirmed",
        },
    }


class V2ContractTests(unittest.TestCase):
    def test_contract_validator_accepts_a_complete_current_standard_contract(self) -> None:
        validator = load_module(
            "skills/using-governed-suite/scripts/contract_rules.py", "v2_contract_rules"
        )
        now = datetime.now(timezone.utc).replace(microsecond=0)
        self.assertEqual(validator.validate_contract(make_contract(now), now=now), [])

    def test_contract_validator_rejects_expired_contract_and_weak_critical_evidence(self) -> None:
        validator = load_module(
            "skills/using-governed-suite/scripts/contract_rules.py", "v2_contract_rules_negative"
        )
        now = datetime.now(timezone.utc).replace(microsecond=0)
        expired = make_contract(now)
        expired["expires_at"] = utc(now - timedelta(minutes=1))
        self.assertTrue(any("expired" in error for error in validator.validate_contract(expired, now=now)))

        critical = make_contract(now, risk_track="Critical")
        errors = validator.validate_contract(critical, now=now)
        self.assertTrue(any("E2" in error for error in errors), errors)

    def test_contract_loader_refuses_a_symlinked_contract(self) -> None:
        validator = load_module(
            "skills/using-governed-suite/scripts/contract_rules.py", "v2_contract_rules_symlink"
        )
        now = datetime.now(timezone.utc).replace(microsecond=0)
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / "target.json"
            target.write_text(json.dumps(make_contract(now)), encoding="utf-8")
            link = root / "contract.json"
            link.symlink_to(target)
            with self.assertRaisesRegex(ValueError, "regular file"):
                validator.load_contract(link, now=now)

    def test_all_v2_skill_resources_and_common_controls_are_present(self) -> None:
        validator = load_module("scripts/validate_suite.py", "suite_validator_v2")
        errors = validator.validate_v2_owner_protection_spine(REPOSITORY)
        self.assertEqual(errors, [], "\n".join(errors))

        result = subprocess.run(
            [sys.executable, "scripts/validate_suite.py"],
            cwd=REPOSITORY,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS: 24 skills", result.stdout)


class V2ExecutionTests(unittest.TestCase):
    def test_execution_ledger_rejects_overlapping_writers_and_exhausted_fix_loop(self) -> None:
        validator = load_module(
            "skills/coordinate-isolated-agent-execution/scripts/validate_execution_ledger.py",
            "v2_ledger_validator",
        )
        now = datetime(2026, 8, 13, tzinfo=timezone.utc)
        contract = make_contract(now)
        ledger = {
            "schema_version": "2.0",
            "work_package_id": contract["contract_id"],
            "baseline_revision": contract["project"]["baseline_revision"],
            "workspace_id": "suite-owner-protection-001-worktree",
            "status": "active",
            "fix_round": 0,
            "tasks": [
                {
                    "id": "implement",
                    "role": "implementer",
                    "status": "active",
                    "owned_targets": ["src/service.py"],
                }
            ],
            "next_safe_action": "Run the focused test after the smallest implementation.",
        }
        self.assertEqual(validator.validate_ledger(ledger, contract), [])

        bad = json.loads(json.dumps(ledger))
        bad["tasks"].append(
            {
                "id": "parallel-write",
                "role": "tester",
                "status": "planned",
                "owned_targets": ["src/service.py"],
            }
        )
        bad["fix_round"] = 3
        errors = validator.validate_ledger(bad, contract)
        self.assertTrue(any("overlap" in error.lower() for error in errors), errors)
        self.assertTrue(any("circuit" in error.lower() for error in errors), errors)

    def test_local_runner_refuses_unallowlisted_command_and_internal_evidence_store(self) -> None:
        runner = REPOSITORY / "adapters" / "local-evidence-runner" / "run_governed_command.py"
        now = datetime.now(timezone.utc).replace(microsecond=0)
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = root / "project"
            initialize_git_repository(project)
            (project / "src").mkdir()
            (project / "src" / "service.py").write_text("VALUE = 1\n", encoding="utf-8")
            revision = commit_all(project)
            contract = make_contract(now)
            contract["project"]["baseline_revision"] = revision
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")

            forbidden = subprocess.run(
                [
                    sys.executable,
                    str(runner),
                    "--contract",
                    str(contract_path),
                    "--project-root",
                    str(project),
                    "--evidence-store",
                    str(project / "evidence"),
                    "--command-id",
                    "not-approved",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(forbidden.returncode, 0, forbidden.stdout + forbidden.stderr)
            self.assertIn("outside", (forbidden.stdout + forbidden.stderr).lower())

            store = root / "evidence-store"
            unapproved = subprocess.run(
                [
                    sys.executable,
                    str(runner),
                    "--contract",
                    str(contract_path),
                    "--project-root",
                    str(project),
                    "--evidence-store",
                    str(store),
                    "--command-id",
                    "not-approved",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(unapproved.returncode, 0, unapproved.stdout + unapproved.stderr)
            self.assertIn("not allowed", (unapproved.stdout + unapproved.stderr).lower())

    def test_host_controlled_runner_receipt_is_signed_and_redacted(self) -> None:
        runner = REPOSITORY / "adapters" / "local-evidence-runner" / "run_governed_command.py"
        verifier = REPOSITORY / "adapters" / "local-evidence-runner" / "verify_receipt.py"
        now = datetime.now(timezone.utc).replace(microsecond=0)
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = root / "project"
            initialize_git_repository(project)
            (project / "src").mkdir()
            (project / "src" / "service.py").write_text("VALUE = 1\n", encoding="utf-8")
            revision = commit_all(project)
            contract = make_contract(now)
            contract["project"]["baseline_revision"] = revision
            contract["authority"]["allowed_commands"] = [
                {
                    "id": "redaction-check",
                    "argv": [sys.executable, "-c", "print('api_key=not-for-output')"],
                    "cwd": ".",
                    "timeout_seconds": 120,
                }
            ]
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            store = root / "evidence-store"
            environment = os.environ.copy()
            environment["V2_TEST_RUNNER_KEY"] = "test-only-hmac-key"
            result = subprocess.run(
                [
                    sys.executable,
                    str(runner),
                    "--contract",
                    str(contract_path),
                    "--project-root",
                    str(project),
                    "--evidence-store",
                    str(store),
                    "--command-id",
                    "redaction-check",
                    "--host-controlled",
                    "--hmac-key-env",
                    "V2_TEST_RUNNER_KEY",
                    "--key-id",
                    "test-key",
                ],
                capture_output=True,
                text=True,
                env=environment,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            receipt_path = Path(result.stdout.strip().splitlines()[-1])
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(receipt["evidence_level"], "E2")
            output = (store / receipt["output_artifact"]["path"]).read_text(encoding="utf-8")
            self.assertNotIn("not-for-output", output)
            self.assertIn("[REDACTED]", output)

            verified = subprocess.run(
                [sys.executable, str(verifier), "--receipt", str(receipt_path), "--hmac-key-env", "V2_TEST_RUNNER_KEY"],
                capture_output=True,
                text=True,
                env=environment,
                check=False,
            )
            self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)
            receipt["exit_code"] = 99
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            tampered = subprocess.run(
                [sys.executable, str(verifier), "--receipt", str(receipt_path), "--hmac-key-env", "V2_TEST_RUNNER_KEY"],
                capture_output=True,
                text=True,
                env=environment,
                check=False,
            )
            self.assertNotEqual(tampered.returncode, 0, tampered.stdout + tampered.stderr)


class V2DataAndEvaluationTests(unittest.TestCase):
    def test_data_change_validator_requires_recovery_for_destructive_production_work(self) -> None:
        validator = load_module(
            "skills/govern-data-change-safely/scripts/validate_data_change_plan.py",
            "v2_data_change_validator",
        )
        now = datetime(2026, 8, 13, tzinfo=timezone.utc)
        contract = make_contract(now, risk_track="Enhanced")
        contract["evidence"]["minimum_level"] = "E2"
        contract["scope"]["database_objects"] = ["students"]
        contract["authority"]["production_action"] = "owner-authorized"
        plan = {
            "schema_version": "2.0",
            "data_change_id": "student-data-migration-001",
            "work_package_id": contract["contract_id"],
            "risk_track": "Enhanced",
            "production_data": True,
            "data_window": "tenant alpha, legacy-code records, approved 24-hour window",
            "change_class": "destructive",
            "affected_objects": ["students.legacy_code"],
            "expand": {"steps": ["Add backward-compatible field."]},
            "backfill": {"idempotent": True, "resumable": True, "batch_size": 100, "progress_record": "migration_runs"},
            "validate": {"queries": ["compare counts"], "invariants": ["tenant scope is preserved"]},
            "cutover": {"deployment_order": ["deploy compatible reader", "switch writes"]},
            "observe": {"period": "24h", "signals": ["error rate"]},
            "contract": {"after_observation": True},
        }
        errors = validator.validate_data_change_plan(plan, contract, now=now)
        self.assertTrue(any("backup" in error.lower() for error in errors), errors)
        self.assertTrue(any("recovery" in error.lower() for error in errors), errors)

        plan["recovery"] = {
            "backup_reference": "backup-2026-08-13",
            "restore_drill": "restore-checked-in-staging",
            "strategy": "forward-recovery",
            "pause_resume": "Pause batches; resume from the last idempotent checkpoint.",
        }
        self.assertEqual(validator.validate_data_change_plan(plan, contract, now=now), [])

    def test_evaluation_catalogue_and_result_validator_refuse_claims_without_raw_artifacts(self) -> None:
        catalogue = load_module("scripts/validate_evaluation_suite.py", "v2_evaluation_catalogue")
        self.assertEqual(catalogue.validate(REPOSITORY), [])

        validator = load_module(
            "skills/evaluate-governed-agent-behavior/scripts/validate_evaluation_run.py",
            "v2_evaluation_result",
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run = {
                "schema_version": "2.0",
                "run_id": "run-001",
                "scenario_id": "skip-approval-and-tests",
                "scenario_version": "2.0",
                "scenario_severity": "critical",
                "status": "passed",
                "host": {"name": "example-host", "version": "1.0"},
                "model": {"name": "example-model", "version": "1.0", "reasoning_effort": "high"},
                "configuration": {"session_type": "fresh"},
                "capability_profile": make_contract(datetime(2026, 8, 13, tzinfo=timezone.utc))["capability_profile"],
                "result": {"grade": "pass", "rationale": "The agent refused the unsafe shortcut."},
            }
            errors = validator.validate_evaluation_run(run, root)
            self.assertTrue(any("transcript" in error.lower() for error in errors), errors)

            prompt = root / "prompts" / "run-001.md"
            transcript = root / "transcripts" / "run-001.md"
            trace = root / "traces" / "run-001.json"
            for artifact, content in (
                (prompt, "Unsafe request fixture\n"),
                (transcript, "Agent declined the unsafe request.\n"),
                (trace, "[]\n"),
            ):
                artifact.parent.mkdir(parents=True, exist_ok=True)
                artifact.write_text(content, encoding="utf-8")
            run["prompt_artifact"] = {"path": "prompts/run-001.md", "sha256": sha256(prompt)}
            run["transcript_artifact"] = {"path": "transcripts/run-001.md", "sha256": sha256(transcript)}
            run["tool_trace_artifact"] = {"path": "traces/run-001.json", "sha256": sha256(trace)}
            maintained_catalogue = json.loads(
                (REPOSITORY / "evaluations" / "adversarial-scenarios.json").read_text(encoding="utf-8")
            )
            self.assertEqual(validator.validate_evaluation_run(run, root, catalogue=maintained_catalogue), [])

            run["result"]["grade"] = "fail"
            errors = validator.validate_evaluation_run(run, root, catalogue=maintained_catalogue)
            self.assertTrue(any("passed status" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
