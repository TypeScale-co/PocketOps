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
            "official_api": {
                "status": "unavailable",
                "evidence": [
                    {
                        "kind": "api_probe",
                        "reference": "probe://bank/direct-api",
                        "finding": "No supported direct personal-account API",
                    }
                ],
            },
            "delegated_provider": {
                "status": "available",
                "operationally_obtainable": True,
                "evidence": [
                    {
                        "kind": "official_documentation",
                        "reference": "https://provider.example/docs/banking",
                        "finding": "Provider documents production bank access",
                    },
                    {
                        "kind": "provider_account",
                        "reference": "provider-account://verified",
                        "finding": "Required product and institution are enabled",
                    },
                ],
            },
            "credential_flow": {
                "status": "available",
                "operationally_obtainable": True,
                "evidence": [
                    {
                        "kind": "official_documentation",
                        "reference": "https://provider.example/docs/oauth",
                        "finding": "Provider documents hosted authorization",
                    },
                    {
                        "kind": "browser_probe",
                        "reference": "probe://hosted-authorization",
                        "finding": "Hosted authorization launch was exercised",
                    },
                ],
            },
        },
        "provider_provisioning": {
            "provider": "banking-provider",
            "status": "ready",
            "user_work_type": "none",
            "agent_can_complete": True,
            "authorization_mode": "secret_and_browser",
            "stores_local_credentials": True,
            "creates_external_grant": True,
            "evidence": [
                {
                    "kind": "provider_account",
                    "reference": "provider-account://verified",
                    "finding": "Provider account and product access are ready",
                }
            ],
        },
        "driver": "banking-insights",
    }
    data.update(overrides)
    return data


def access_blocked_contract_data():
    data = contract_data(
        target_completion_status="capability_built_access_blocked"
    )
    data["access_discovery"]["delegated_provider"] = {
        "status": "conditionally_available",
        "blockers": ["Provider production approval is pending"],
        "evidence": [
            {
                "kind": "official_documentation",
                "reference": "https://provider.example/docs/production",
                "finding": "Production approval is required",
            }
        ],
    }
    data["access_discovery"]["credential_flow"] = {
        "status": "operator_blocked",
        "blockers": ["Provider account is not production-enabled"],
        "evidence": [
            {
                "kind": "official_documentation",
                "reference": "https://provider.example/docs/oauth",
                "finding": "OAuth requires production access",
            }
        ],
    }
    data["provider_provisioning"] = {
        "provider": "banking-provider",
        "status": "operator_blocked",
        "user_work_type": "commercial_approval",
        "agent_can_complete": False,
        "authorization_mode": "secret_and_browser",
        "stores_local_credentials": True,
        "creates_external_grant": True,
        "required_actions": ["Obtain provider production approval"],
        "evidence": [
            {
                "kind": "official_documentation",
                "reference": "https://provider.example/docs/production",
                "finding": "Production approval is required",
            }
        ],
    }
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

    def test_ready_status_rejects_conditional_provider_access(self):
        data = contract_data()
        data["access_discovery"]["delegated_provider"] = {
            "status": "conditionally_available",
            "operationally_obtainable": False,
            "blockers": ["Full provider production approval is pending"],
            "evidence": [
                {
                    "kind": "official_documentation",
                    "reference": "https://provider.example/docs/production",
                    "finding": "Institution requires full production access",
                }
            ],
        }
        data["access_discovery"]["credential_flow"] = {
            "status": "operator_blocked",
            "blockers": ["Provider production account is unavailable"],
            "evidence": [
                {
                    "kind": "official_documentation",
                    "reference": "https://provider.example/docs/oauth",
                    "finding": "OAuth requires production access",
                }
            ],
        }
        data["provider_provisioning"] = {
            "provider": "banking-provider",
            "status": "operator_blocked",
            "user_work_type": "commercial_approval",
            "agent_can_complete": False,
            "authorization_mode": "secret_and_browser",
            "stores_local_credentials": True,
            "creates_external_grant": True,
            "required_actions": ["Obtain provider production approval"],
            "evidence": [
                {
                    "kind": "official_documentation",
                    "reference": "https://provider.example/docs/production",
                    "finding": "Production approval is required",
                }
            ],
        }
        with self.assertRaisesRegex(
            ValidationError, "capability_ready_not_connected requires"
        ):
            OutcomeContract(**data)

    def test_blocked_provider_uses_truthful_completion_status(self):
        data = access_blocked_contract_data()
        contract = OutcomeContract(**data)
        self.assertEqual(
            contract.target_completion_status.value,
            "capability_built_access_blocked",
        )

    def test_available_access_requires_authoritative_evidence(self):
        data = contract_data()
        data["access_discovery"]["delegated_provider"]["evidence"] = [
            {
                "kind": "provider_account",
                "reference": "provider-account://verified",
                "finding": "Account appears enabled",
            }
        ]
        with self.assertRaisesRegex(
            ValidationError, "official_documentation evidence"
        ):
            OutcomeContract(**data)

    def test_access_discovery_rejects_free_form_status_claims(self):
        data = contract_data()
        data["access_discovery"]["delegated_provider"] = (
            "available through a provider"
        )
        with self.assertRaises(ValidationError):
            OutcomeContract(**data)

    def test_ready_provider_rejects_technical_user_onboarding(self):
        data = contract_data()
        data["provider_provisioning"]["user_work_type"] = "technical"
        with self.assertRaisesRegex(
            ValidationError, "cannot be ready while technical user work"
        ):
            OutcomeContract(**data)

    def test_connect_contract_requires_ready_provider_provisioning(self):
        data = contract_data(
            raw_request="Connect my banking account",
            contract_type="connect_capability",
            target_completion_status="capability_connected",
            provider_provisioning=None,
        )
        with self.assertRaisesRegex(
            ValidationError, "provider provisioning to be ready"
        ):
            OutcomeContract(**data)


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
                    "setup-auth": {
                        "effects": [],
                        "behavior": {
                            "default_invocation": True,
                            "launches_secure_collection": True,
                        },
                    },
                    "authorize": {
                        "effects": ["read"],
                        "behavior": {
                            "default_invocation": True,
                            "opens_browser": True,
                        },
                    },
                    "connect": {
                        "effects": ["read"],
                        "behavior": {
                            "default_invocation": True,
                            "validates_connection": True,
                        },
                    },
                    "execute": {"effects": ["read"]},
                    "verify": {"effects": ["read"]},
                    "rollback": {
                        "effects": ["local_write"],
                        "supported": True,
                        "behavior": {
                            "default_invocation": True,
                            "removes_local_credentials": True,
                        },
                    },
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
                        "command_behavior": {
                            "setup-auth": {
                                "passed": True,
                                "default_invocation": True,
                                "launches_secure_collection": True,
                            },
                            "authorize": {
                                "passed": True,
                                "default_invocation": True,
                                "opens_browser": True,
                            },
                            "connect": {
                                "passed": True,
                                "default_invocation": True,
                                "validates_connection": True,
                            },
                            "rollback": {
                                "passed": True,
                                "default_invocation": True,
                                "removes_local_credentials": True,
                            },
                        },
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

    def test_access_blocked_capability_can_finish_truthfully(self):
        self._write_yaml(
            "plans/active/banking-insights.yaml",
            access_blocked_contract_data(),
        )
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        subprocess.run(
            ["git", "commit", "-qm", "blocked access contract"],
            cwd=self.root,
            check=True,
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
                "completion_status": "capability_built_access_blocked",
                "user_facing_status": "capability_built_access_blocked",
                "connection": {
                    "status": "not_connected",
                    "credential_status": "provider_blocked",
                },
                "verification": {
                    "status": "verified",
                    "checks": [{"name": "build-tests", "passed": True}],
                    "evidence": {
                        "captured_at": "2026-07-30T12:05:00",
                        "artifacts": ["adapter tests", "driver tests"],
                        "command_behavior": {
                            "setup-auth": {
                                "passed": True,
                                "default_invocation": True,
                                "launches_secure_collection": True,
                            },
                            "authorize": {
                                "passed": True,
                                "default_invocation": True,
                                "opens_browser": True,
                            },
                            "connect": {
                                "passed": True,
                                "default_invocation": True,
                                "validates_connection": True,
                            },
                            "rollback": {
                                "passed": True,
                                "default_invocation": True,
                                "removes_local_credentials": True,
                            },
                        },
                    },
                },
            }
        )
        self._write_yaml(str(run_path.relative_to(self.root)), run_data)

        result = complete_run(run.run_id, project_root=self.root)
        self.assertTrue(result.success)
        self.assertIn("capability_built_access_blocked", result.message)

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

    def test_build_rejects_command_names_without_behavioral_evidence(self):
        run, run_path = self._ready_run()
        run_data = yaml.safe_load(run_path.read_text())
        run_data["verification"]["evidence"].pop("command_behavior")
        self._write_yaml(str(run_path.relative_to(self.root)), run_data)

        with self.assertRaisesRegex(CompletionError, "behaviorally verify"):
            complete_run(run.run_id, project_root=self.root)

    def test_build_rejects_instruction_only_rollback(self):
        run, run_path = self._ready_run()
        run_data = yaml.safe_load(run_path.read_text())
        run_data["verification"]["evidence"]["command_behavior"]["rollback"][
            "removes_local_credentials"
        ] = False
        self._write_yaml(str(run_path.relative_to(self.root)), run_data)

        with self.assertRaisesRegex(
            CompletionError, "rollback must behaviorally verify"
        ):
            complete_run(run.run_id, project_root=self.root)

    def test_build_rejects_hidden_flag_for_normal_credential_flow(self):
        run, _ = self._ready_run()
        manifest_path = self.root / "drivers/banking-insights/manifest.yaml"
        manifest = yaml.safe_load(manifest_path.read_text())
        manifest["commands"]["setup-auth"]["behavior"]["default_invocation"] = False
        self._write_yaml("drivers/banking-insights/manifest.yaml", manifest)

        with self.assertRaisesRegex(
            CompletionError, "setup-auth must behaviorally verify"
        ):
            complete_run(run.run_id, project_root=self.root)

    def test_secret_only_integration_does_not_require_browser_oauth(self):
        contract_path = self.root / "plans/active/banking-insights.yaml"
        contract = yaml.safe_load(contract_path.read_text())
        provisioning = contract["provider_provisioning"]
        provisioning["authorization_mode"] = "secret_collection"
        provisioning["creates_external_grant"] = False
        self._write_yaml("plans/active/banking-insights.yaml", contract)

        manifest_path = self.root / "drivers/banking-insights/manifest.yaml"
        manifest = yaml.safe_load(manifest_path.read_text())
        manifest["commands"].pop("authorize")
        self._write_yaml("drivers/banking-insights/manifest.yaml", manifest)
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        subprocess.run(
            ["git", "commit", "-qm", "secret-only authorization"],
            cwd=self.root,
            check=True,
        )

        run, _ = self._ready_run()
        result = complete_run(run.run_id, project_root=self.root)
        self.assertTrue(result.success)

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
