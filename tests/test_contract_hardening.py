import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml
from pydantic import ValidationError

from pocketops.schemas.contract import OutcomeContract
from pocketops.workflow.completion import (
    CompletionError,
    complete_run,
    create_run,
)


def contract_data(**overrides):
    data = {
        "id": "banking-insights",
        "created_at": "2026-07-30T12:00:00",
        "raw_request": "Add a capability to draw insights from my banking account",
        "contract_type": "build_capability",
        "target_completion_status": "capability_ready_not_connected",
        "outcome": "A reusable capability can read the account and generate insights",
        "verification": {
            "checks": [
                {
                    "name": "capability-path",
                    "description": "Adapter and driver expose a real account access path",
                    "method": "independent-path",
                    "expected": "Real provider integration and connection command",
                }
            ]
        },
        "source_system_request": {
            "requested": True,
            "system": "personal banking account",
            "expected_agent_access": True,
        },
        "access_discovery": {
            "official_api": "unavailable",
            "delegated_provider": "available",
            "credential_flow": "planned",
        },
        "driver": "banking-insights",
    }
    data.update(overrides)
    return data


class ContractSchemaTests(unittest.TestCase):
    def test_source_request_cannot_be_disabled(self):
        data = contract_data()
        data["source_system_request"]["requested"] = False
        with self.assertRaisesRegex(
            ValidationError, "source_system_request.requested must be true"
        ):
            OutcomeContract(**data)

    def test_ad_hoc_capability_build_flag_is_rejected(self):
        with self.assertRaisesRegex(ValidationError, "unreviewed gate exemption"):
            OutcomeContract(**contract_data(capability_build=True))

    def test_contract_type_constrains_completion_status(self):
        with self.assertRaisesRegex(ValidationError, "may only target"):
            OutcomeContract(
                **contract_data(target_completion_status="outcome_delivered")
            )

    def test_framework_change_requires_framework_request(self):
        with self.assertRaisesRegex(ValidationError, "framework_change is reserved"):
            OutcomeContract(
                **contract_data(
                    raw_request="Create a reusable customer report",
                    contract_type="framework_change",
                    target_completion_status="capability_built",
                    source_system_request={"requested": False},
                    access_discovery=None,
                    driver=None,
                )
            )

    def test_connect_contract_requires_external_system(self):
        with self.assertRaisesRegex(
            ValidationError, "connect_capability requires"
        ):
            OutcomeContract(
                **contract_data(
                    raw_request="Authorize the existing reporting capability",
                    contract_type="connect_capability",
                    target_completion_status="capability_connected",
                    source_system_request={"requested": False},
                    access_discovery=None,
                )
            )


class CompletionHardeningTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        for directory in (
            "plans/active",
            "runs/current",
            "runs/archive",
            "drivers/banking-insights",
            "adapters/banking-provider",
            "pocketops/workflow",
        ):
            (self.root / directory).mkdir(parents=True, exist_ok=True)

        self._write_yaml(
            "plans/active/banking-insights.yaml",
            contract_data(),
        )
        self._write_yaml(
            "drivers/banking-insights/manifest.yaml",
            {
                "name": "banking-insights",
                "kind": "driver",
                "version": "1.0.0",
                "depends_on": {
                    "adapters": [{"name": "banking-provider", "operations": ["read"]}]
                },
                "commands": {
                    "plan": {"effects": []},
                    "setup-auth": {"effects": []},
                    "execute": {"effects": ["read"]},
                    "verify": {"effects": ["read"]},
                },
            },
        )
        self._write_yaml(
            "adapters/banking-provider/manifest.yaml",
            {
                "name": "banking-provider",
                "kind": "adapter",
                "version": "1.0.0",
                "credentials": [
                    {"name": "BANK_LINK_TOKEN", "required": True}
                ],
                "provides": {
                    "read": {
                        "effects": {"risk": "read", "scope": "external"}
                    }
                },
            },
        )
        (self.root / "pocketops/workflow/completion.py").write_text(
            "# protected baseline\n"
        )
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(
            ["git", "config", "user.email", "tests@pocketops.local"],
            cwd=self.root,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "PocketOps Tests"],
            cwd=self.root,
            check=True,
        )
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        subprocess.run(
            ["git", "commit", "-qm", "baseline"], cwd=self.root, check=True
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def _write_yaml(self, relative_path, data):
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(data, sort_keys=False))

    def _ready_run(self):
        run = create_run(
            contract_id="banking-insights",
            driver="banking-insights",
            project_root=self.root,
        )
        run_path = Path(run.run_file)
        run_data = yaml.safe_load(run_path.read_text())
        run_data.update(
            {
                "completion_status": "capability_ready_not_connected",
                "user_facing_status": "capability_ready_not_connected",
                "connection": {
                    "status": "not_connected",
                    "credential_status": "missing",
                },
                "verification": {
                    "status": "verified",
                    "checks": [{"name": "build-tests", "passed": True}],
                    "evidence": {
                        "captured_at": "2026-07-30T12:05:00",
                        "artifacts": ["adapter tests", "driver tests"],
                    },
                },
            }
        )
        self._write_yaml(
            str(run_path.relative_to(self.root)),
            run_data,
        )
        return run, run_path

    def test_build_capability_can_finish_ready_not_connected(self):
        run, _ = self._ready_run()
        result = complete_run(run.run_id, project_root=self.root)
        self.assertTrue(result.success)
        self.assertIn("capability_ready_not_connected", result.message)

    def test_protected_framework_change_rejects_ordinary_run(self):
        run, run_path = self._ready_run()
        (self.root / "pocketops/workflow/completion.py").write_text(
            "# agent weakened the completion gate\n"
        )
        run_data = yaml.safe_load(run_path.read_text())
        run_data["review"] = {
            "status": "approved",
            "checks": [{"name": "fake", "passed": True}],
        }
        self._write_yaml(str(run_path.relative_to(self.root)), run_data)

        with self.assertRaisesRegex(CompletionError, "Ordinary task modified"):
            complete_run(run.run_id, project_root=self.root)

        reviewed = yaml.safe_load(run_path.read_text())["review"]
        self.assertEqual("rejected", reviewed["status"])
        self.assertNotEqual("fake", reviewed["checks"][0]["name"])

    def test_force_completion_is_disabled(self):
        run, _ = self._ready_run()
        with self.assertRaisesRegex(CompletionError, "force completion is disabled"):
            complete_run(run.run_id, project_root=self.root, force=True)

    def test_contract_scope_cannot_change_after_run_creation(self):
        run, _ = self._ready_run()
        contract_path = self.root / "plans/active/banking-insights.yaml"
        contract = yaml.safe_load(contract_path.read_text())
        contract["outcome"] = "A narrower outcome selected after execution began"
        self._write_yaml("plans/active/banking-insights.yaml", contract)

        with self.assertRaisesRegex(CompletionError, "contract was changed"):
            complete_run(run.run_id, project_root=self.root)

    def test_credential_dependent_build_requires_connect_command(self):
        run, _ = self._ready_run()
        manifest_path = self.root / "drivers/banking-insights/manifest.yaml"
        manifest = yaml.safe_load(manifest_path.read_text())
        manifest["commands"].pop("setup-auth")
        self._write_yaml("drivers/banking-insights/manifest.yaml", manifest)

        with self.assertRaisesRegex(CompletionError, "lifecycle"):
            complete_run(run.run_id, project_root=self.root)

    def test_execute_workflow_requires_live_source_read(self):
        contract_path = self.root / "plans/active/banking-insights.yaml"
        contract = yaml.safe_load(contract_path.read_text())
        contract["contract_type"] = "execute_workflow"
        contract["target_completion_status"] = "outcome_delivered"
        self._write_yaml("plans/active/banking-insights.yaml", contract)
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        subprocess.run(
            ["git", "commit", "-qm", "execute contract"], cwd=self.root, check=True
        )

        run = create_run(
            contract_id="banking-insights",
            driver="banking-insights",
            project_root=self.root,
        )
        run_path = Path(run.run_file)
        run_data = yaml.safe_load(run_path.read_text())
        run_data.update(
            {
                "completion_status": "outcome_delivered",
                "user_facing_status": "outcome_delivered",
                "verification": {
                    "status": "verified",
                    "checks": [{"name": "unit-tests", "passed": True}],
                    "evidence": {
                        "captured_at": "2026-07-30T12:05:00",
                        "artifacts": ["unit tests only"],
                    },
                },
            }
        )
        self._write_yaml(str(run_path.relative_to(self.root)), run_data)

        with self.assertRaisesRegex(CompletionError, "source-system retrieval"):
            complete_run(run.run_id, project_root=self.root)

    def test_explicit_framework_contract_may_change_protected_files(self):
        framework_contract = {
            "id": "framework-hardening",
            "created_at": "2026-07-30T12:00:00",
            "raw_request": "Harden the PocketOps completion gates and review protocol",
            "contract_type": "framework_change",
            "target_completion_status": "capability_built",
            "outcome": "PocketOps rejects completion-gate weakening",
            "verification": {
                "checks": [
                    {
                        "name": "regressions",
                        "description": "Gate-tampering regression tests pass",
                        "method": "independent-path",
                    }
                ]
            },
            "source_system_request": {"requested": False},
        }
        self._write_yaml(
            "plans/active/framework-hardening.yaml",
            framework_contract,
        )
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        subprocess.run(
            ["git", "commit", "-qm", "framework contract"], cwd=self.root, check=True
        )

        run = create_run(
            contract_id="framework-hardening",
            project_root=self.root,
        )
        run_path = Path(run.run_file)
        run_data = yaml.safe_load(run_path.read_text())
        run_data.update(
            {
                "completion_status": "capability_built",
                "user_facing_status": "capability_built",
                "verification": {
                    "status": "verified",
                    "checks": [{"name": "regressions", "passed": True}],
                    "evidence": {
                        "captured_at": "2026-07-30T12:05:00",
                        "artifacts": ["hardening regression suite"],
                    },
                },
            }
        )
        self._write_yaml(str(run_path.relative_to(self.root)), run_data)
        (self.root / "pocketops/workflow/completion.py").write_text(
            "# reviewed framework hardening\n"
        )

        result = complete_run(run.run_id, project_root=self.root)
        self.assertTrue(result.success)


if __name__ == "__main__":
    unittest.main()
