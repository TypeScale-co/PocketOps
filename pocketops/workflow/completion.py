"""
Workflow completion enforcement.

This module provides the ONLY valid way to start and complete a PocketOps workflow.

- create_run() MUST be called before execution starts
- complete_run() MUST be called to finish (enforces all gates)

IMPORTANT: Agents declaring "done" without calling complete_run() have NOT
actually completed the workflow. The run record will show incomplete status.
"""

import subprocess
import yaml
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, List

from pocketops.gates import Phase, GateRegistry, GateResult

# Import gate implementations so decorators register checks before transitions.
import pocketops.gates.checks  # noqa: F401  # pyright: ignore[reportUnusedImport]


_SOURCE_SYSTEM_REQUEST_TERMS = (
    "from my",
    "my account",
    "my banking",
    "my bank",
    "my email",
    "my calendar",
    "my crm",
    "my documents",
    "my files",
    "pull",
    "fetch",
    "retrieve",
    "connect",
    "sync",
    "import from",
    "read from",
)

_FALLBACK_TERMS = (
    "manual export",
    "manually export",
    "manual upload",
    "copy paste",
    "copy-paste",
    "export file",
    "export files",
    "csv export",
    "local csv",
    "local file",
    "input file",
    "uploaded file",
    "mock data",
    "synthetic data",
    "fixture",
    "sandbox only",
)

_PROTECTED_FRAMEWORK_PATHS = (
    "AGENTS.md",
    ".agents/",
    "pocketops/",
    "scripts/verify",
)

_CONNECTION_COMMANDS = {"setup-auth", "setup_auth", "authorize", "connect"}
_MISSING_CREDENTIAL_STATUSES = {
    "missing",
    "not_configured",
    "not-configured",
    "blocked",
}


class RunCreationError(Exception):
    """Raised when run creation fails."""

    def __init__(self, message: str, details: dict | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


class CompletionError(Exception):
    """Raised when completion is blocked by a gate."""

    def __init__(self, gate_name: str, message: str, details: dict | None = None):
        self.gate_name = gate_name
        self.message = message
        self.details = details or {}
        super().__init__(f"Completion blocked by {gate_name}: {message}")


@dataclass
class RunRecord:
    """A run record returned by create_run()."""
    run_id: str
    run_file: str
    contract_id: str
    driver: Optional[str]
    created_at: str


@dataclass
class CompletionResult:
    """Result of a completion attempt."""
    success: bool
    run_id: str
    message: str
    gate_results: list[GateResult] = field(default_factory=list)
    archived_to: Optional[str] = None


def _find_project_root() -> Path:
    """Find the PocketOps project root."""
    cwd = Path.cwd()
    current = cwd
    while current != current.parent:
        if (current / "plans").exists() and (current / "runs").exists():
            return current
        current = current.parent
    return cwd


def _git_output(project_root: Path, *args: str) -> str:
    """Run a read-only Git command, returning an empty string on failure."""
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return ""
    return result.stdout.rstrip("\n")


def _git_revision(project_root: Path) -> str:
    return _git_output(project_root, "rev-parse", "HEAD")


def create_run(
    contract_id: str,
    driver: Optional[str] = None,
    effects: List[dict] | None = None,
    inputs: dict | None = None,
    project_root: Optional[str | Path] = None,
) -> RunRecord:
    """
    Create a run record before execution.

    This MUST be called before executing any workflow. It creates the run
    record that will be validated and archived by complete_run().

    Args:
        contract_id: ID of the outcome contract (must exist in plans/active/)
        driver: Name of the driver being executed
        effects: List of effects (risk, scope, reversibility)
        inputs: Input parameters for the driver
        project_root: Path to project root (auto-detected if not provided)

    Returns:
        RunRecord with run_id and file path

    Raises:
        RunCreationError: If contract doesn't exist or other validation fails
    """
    project_root = Path(project_root) if project_root else _find_project_root()
    plans_dir = project_root / "plans" / "active"
    runs_dir = project_root / "runs" / "current"

    # Validate contract exists
    contract_file = plans_dir / f"{contract_id}.yaml"
    if not contract_file.exists():
        contract_file = plans_dir / f"{contract_id}.yml"

    if not contract_file.exists():
        raise RunCreationError(
            f"Contract '{contract_id}' not found in plans/active/. "
            "You must create a contract during PLAN phase before execution.",
            details={"contract_id": contract_id, "plans_dir": str(plans_dir)},
        )

    # Validate contract content before any execution can start.
    try:
        from pocketops.validation import load_contract

        contract = load_contract(contract_file)
    except Exception as e:
        raise RunCreationError(
            f"Contract '{contract_id}' is invalid. Fix the outcome contract before execution.",
            details={"contract_id": contract_id, "contract_file": str(contract_file), "error": str(e)},
        ) from e

    contract_type = contract.contract_type.value
    if contract_type != "framework_change":
        if not driver:
            raise RunCreationError(
                f"Contract type '{contract_type}' requires a driver.",
                details={"contract_id": contract_id, "contract_type": contract_type},
            )
        driver_dir = project_root / "drivers" / driver
        driver_manifest = driver_dir / "manifest.yaml"
        if not driver_manifest.exists():
            raise RunCreationError(
                f"Driver '{driver}' not found. "
                "You must create the driver during BUILD phase before execution.",
                details={"driver": driver, "expected_path": str(driver_manifest)},
            )

    # Generate run ID
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_id = f"{timestamp}-{driver or contract_type}"

    # Create run record
    run_data = {
        "run_id": run_id,
        "contract_id": contract_id,
        "contract_type": contract_type,
        "target_completion_status": contract.target_completion_status.value,
        "contract_snapshot": contract.model_dump(mode="json"),
        "driver": driver,
        "status": "created",
        "created_at": datetime.now().isoformat(),
        "framework_baseline_revision": _git_revision(project_root),
        "inputs": inputs or {},
        "effects": effects or [],
        "outputs": {},
        "verification": {
            "status": "not_verified",
            "checks": [],
            "evidence": {},
        },
        "connection": {
            "status": "not_assessed",
            "credential_status": "not_assessed",
        },
        "completion_status": None,
        "user_facing_status": None,
    }

    # Ensure runs directory exists
    runs_dir.mkdir(parents=True, exist_ok=True)

    # Write run file
    run_file = runs_dir / f"{run_id}.yaml"
    with open(run_file, "w") as f:
        yaml.safe_dump(run_data, f, default_flow_style=False, sort_keys=False)

    return RunRecord(
        run_id=run_id,
        run_file=str(run_file),
        contract_id=contract_id,
        driver=driver,
        created_at=run_data["created_at"],
    )


def _load_run_file(runs_dir: Path, run_id: str) -> tuple[Path, dict]:
    """Load run file, return (path, data)."""
    run_file = runs_dir / f"{run_id}.yaml"
    if not run_file.exists():
        run_file = runs_dir / f"{run_id}.yml"

    if not run_file.exists():
        raise CompletionError(
            gate_name="run-exists",
            message=f"Run file not found: {run_id}",
        )

    with open(run_file) as f:
        data = yaml.safe_load(f) or {}

    return run_file, data


def _normalize(value: str | None) -> str:
    return (value or "").lower()


def _contains_any(value: str, terms: tuple[str, ...]) -> bool:
    return any(term in value for term in terms)


def _request_implies_source_system_access(raw_request: str) -> bool:
    return _contains_any(_normalize(raw_request), _SOURCE_SYSTEM_REQUEST_TERMS)


def _request_explicitly_allows_fallback(raw_request: str) -> bool:
    return _contains_any(_normalize(raw_request), _FALLBACK_TERMS)


def _text_implies_fallback(*values: str | None) -> bool:
    return _contains_any(_normalize(" ".join(v or "" for v in values)), _FALLBACK_TERMS)


def _source_system_requested(contract: dict) -> bool:
    source_system_request = contract.get("source_system_request", {})
    if isinstance(source_system_request, dict) and source_system_request.get("requested"):
        return True
    return _request_implies_source_system_access(contract.get("raw_request", ""))


def _fallback_active(contract: dict) -> bool:
    fallback_mode = contract.get("fallback_mode", {})
    if isinstance(fallback_mode, dict) and fallback_mode.get("type"):
        return True
    return _text_implies_fallback(_contract_text(contract))


def _fallback_accepted(contract: dict) -> bool:
    fallback_mode = contract.get("fallback_mode", {})
    return bool(
        isinstance(fallback_mode, dict)
        and fallback_mode.get("accepted_after_access_discovery")
    )


def _contract_text(contract: dict) -> str:
    verification = contract.get("verification", {})
    checks = verification.get("checks", []) if isinstance(verification, dict) else []
    constraints = contract.get("constraints", [])

    parts = [str(contract.get("outcome", ""))]
    for check in checks:
        if isinstance(check, dict):
            parts.append(str(check.get("description", "")))
            parts.append(str(check.get("expected", "")))
    for constraint in constraints:
        if isinstance(constraint, dict):
            parts.append(str(constraint.get("description", "")))
    return " ".join(parts)


def _manifest_text(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        with open(path) as f:
            data = yaml.safe_load(f) or {}
    except yaml.YAMLError:
        return path.name

    parts = [str(data.get("name", "")), str(data.get("description", ""))]
    for item in data.get("inputs", []) or []:
        if isinstance(item, dict):
            parts.append(str(item.get("name", "")))
            parts.append(str(item.get("description", "")))
    return " ".join(parts)


def _is_protected_framework_path(path: str) -> bool:
    normalized = path.strip().replace("\\", "/")
    return any(
        normalized == protected.rstrip("/") or normalized.startswith(protected)
        for protected in _PROTECTED_FRAMEWORK_PATHS
    )


def _changed_paths(project_root: Path, baseline_revision: str) -> list[str]:
    """Collect committed and working-tree changes made since run creation."""
    paths: set[str] = set()
    if baseline_revision:
        current_revision = _git_revision(project_root)
        if current_revision and current_revision != baseline_revision:
            paths.update(
                line
                for line in _git_output(
                    project_root,
                    "diff",
                    "--name-only",
                    f"{baseline_revision}..{current_revision}",
                ).splitlines()
                if line
            )

    status = _git_output(
        project_root,
        "status",
        "--porcelain",
        "--untracked-files=all",
    )
    for line in status.splitlines():
        if len(line) < 4:
            continue
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        paths.add(path.strip('"'))
    return sorted(paths)


def _driver_components(
    project_root: Path,
    driver_name: str | None,
) -> tuple[dict, list[tuple[str, dict]]]:
    """Load the selected driver and its declared adapter manifests."""
    if not driver_name:
        return {}, []

    driver_manifest = project_root / "drivers" / driver_name / "manifest.yaml"
    if not driver_manifest.exists():
        return {}, []
    with open(driver_manifest) as f:
        driver_data = yaml.safe_load(f) or {}

    adapters: list[tuple[str, dict]] = []
    dependencies = driver_data.get("depends_on", {}).get("adapters", []) or []
    for dependency in dependencies:
        name = dependency if isinstance(dependency, str) else dependency.get("name")
        if not name:
            continue
        manifest = project_root / "adapters" / name / "manifest.yaml"
        if not manifest.exists():
            continue
        with open(manifest) as f:
            adapters.append((name, yaml.safe_load(f) or {}))
    return driver_data, adapters


def _commands(driver_data: dict) -> set[str]:
    commands = driver_data.get("commands", {})
    if isinstance(commands, dict):
        return set(commands)
    if isinstance(commands, list):
        return {
            command if isinstance(command, str) else command.get("name", "")
            for command in commands
        }
    return set()


def _command_behavior(driver_data: dict, command_name: str) -> dict:
    commands = driver_data.get("commands", {})
    if not isinstance(commands, dict):
        return {}
    command = commands.get(command_name, {})
    if not isinstance(command, dict):
        return {}
    behavior = command.get("behavior", {})
    return behavior if isinstance(behavior, dict) else {}


def _observed_command_behavior(evidence: dict, command_name: str) -> dict:
    command_behavior = evidence.get("command_behavior", {})
    if not isinstance(command_behavior, dict):
        return {}
    observed = command_behavior.get(command_name, {})
    return observed if isinstance(observed, dict) else {}


def _behavior_verified(
    driver_data: dict,
    evidence: dict,
    command_name: str,
    behavior_name: str,
) -> bool:
    declared = _command_behavior(driver_data, command_name)
    observed = _observed_command_behavior(evidence, command_name)
    return bool(
        declared.get("default_invocation")
        and declared.get(behavior_name)
        and observed.get("passed")
        and observed.get("default_invocation")
        and observed.get(behavior_name)
    )


def _access_assessments(contract: dict) -> list[dict]:
    discovery = contract.get("access_discovery", {})
    if not isinstance(discovery, dict):
        return []
    return [
        assessment
        for field in (
            "official_api",
            "sdk_or_cli",
            "delegated_provider",
            "browser_flow",
            "credential_flow",
        )
        if isinstance((assessment := discovery.get(field)), dict)
    ]


def _has_operational_access_evidence(contract: dict) -> bool:
    operational_kinds = {
        "provider_account",
        "api_probe",
        "sdk_probe",
        "cli_probe",
        "browser_probe",
        "live_system",
    }
    for assessment in _access_assessments(contract):
        evidence = assessment.get("evidence", [])
        evidence_kinds = {
            item.get("kind")
            for item in evidence
            if isinstance(item, dict)
        }
        if (
            assessment.get("status") == "available"
            and assessment.get("operationally_obtainable")
            and "official_documentation" in evidence_kinds
            and evidence_kinds & operational_kinds
        ):
            return True
    return False


def _adapter_has_external_read(adapter_data: dict) -> bool:
    for operation in (adapter_data.get("provides", {}) or {}).values():
        if not isinstance(operation, dict):
            continue
        effects = operation.get("effects", {})
        if isinstance(effects, dict):
            if (
                effects.get("risk") == "read"
                and effects.get("scope") in ("external", "production")
            ):
                return True
        elif isinstance(effects, list):
            if any(
                isinstance(effect, dict)
                and effect.get("risk") == "read"
                and effect.get("scope") in ("external", "production")
                for effect in effects
            ):
                return True
    return False


def _required_credentials(adapters: list[tuple[str, dict]]) -> list[str]:
    required = []
    for _, adapter_data in adapters:
        for credential in adapter_data.get("credentials", []) or []:
            if isinstance(credential, dict) and credential.get("required", True):
                required.append(str(credential.get("name", "unnamed")))
    return required


def _run_reviewing_contracts(run_data: dict, project_root: Path) -> dict:
    """
    Run the reviewing-contracts checks programmatically.

    Returns review dict with status and checks.
    """
    review = {
        "status": "pending",
        "reviewer": "pocketops.workflow.completion",
        "timestamp": datetime.now().isoformat(),
        "checks": [],
        "reasons": [],
    }

    # Check 0: Plan file exists - was planning phase completed?
    contract_id = run_data.get("contract_id") or run_data.get("plan", {}).get("contract_id")
    plans_dir = project_root / "plans" / "active"
    contract_exists = False
    contract = {}
    normalized_contract = {}

    if contract_id:
        contract_file = plans_dir / f"{contract_id}.yaml"
        if not contract_file.exists():
            contract_file = plans_dir / f"{contract_id}.yml"

        if contract_file.exists():
            contract_exists = True
            with open(contract_file) as f:
                contract = yaml.safe_load(f) or {}
            from pocketops.schemas.contract import OutcomeContract

            try:
                normalized_contract = OutcomeContract(**contract).model_dump(mode="json")
            except Exception:
                normalized_contract = contract
            review["checks"].append({
                "name": "plan-exists",
                "passed": True,
                "notes": f"Contract file found: {contract_file.name}",
            })
        else:
            review["checks"].append({
                "name": "plan-exists",
                "passed": False,
                "notes": f"Contract file not found: {contract_id}.yaml in plans/active/",
            })
            review["reasons"].append("Contract/plan file missing - was PLAN phase completed?")
    else:
        review["checks"].append({
            "name": "plan-exists",
            "passed": False,
            "notes": "No contract_id in run data - run must reference a contract",
        })
        review["reasons"].append("No contract reference - PLAN phase was skipped")

    # Check 0b: Raw request preservation - was the contract narrowed?
    if contract_exists:
        raw_request = contract.get("raw_request", "")
        contract_uses_fallback = _fallback_active(contract)

        if not raw_request:
            review["checks"].append({
                "name": "raw-request-preserved",
                "passed": False,
                "notes": "Contract does not include raw_request; cannot compare delivery to original user intent",
            })
            review["reasons"].append("Missing raw_request prevents outcome preservation review")
        elif (
            _source_system_requested(contract)
            and contract_uses_fallback
            and not _request_explicitly_allows_fallback(raw_request)
            and not _fallback_accepted(contract)
        ):
            review["checks"].append({
                "name": "raw-request-preserved",
                "passed": False,
                "notes": (
                    "Raw request asks for source-system data, but contract narrows "
                    "delivery to fallback input such as manual files, copy/paste, "
                    "mock data, or sandbox-only data"
                ),
            })
            review["reasons"].append(
                "Outcome narrowed from source-system retrieval to fallback mode"
            )
        else:
            review["checks"].append({
                "name": "raw-request-preserved",
                "passed": True,
                "notes": "Contract preserves raw request scope",
            })
    else:
        review["checks"].append({
            "name": "raw-request-preserved",
            "passed": False,
            "notes": "Cannot compare raw request without contract file",
        })
        review["reasons"].append("Cannot review raw request preservation without contract")

    contract_type = run_data.get("contract_type", "")
    target_status = run_data.get("target_completion_status", "")
    actual_status = run_data.get("completion_status", "")

    # Check 0c: Security-relevant contract fields are fixed at run creation.
    contract_snapshot = run_data.get("contract_snapshot", {})
    immutable_contract_fields = (
        "raw_request",
        "contract_type",
        "target_completion_status",
        "outcome",
        "verification",
        "constraints",
        "source_system_request",
        "access_discovery",
        "provider_provisioning",
        "fallback_mode",
        "driver",
    )
    changed_contract_fields = [
        field
        for field in immutable_contract_fields
        if contract_snapshot.get(field) != normalized_contract.get(field)
    ] if contract_exists and contract_snapshot else list(immutable_contract_fields)
    if changed_contract_fields:
        review["checks"].append({
            "name": "contract-integrity",
            "passed": False,
            "notes": (
                "Security-relevant contract fields changed after run creation: "
                + ", ".join(changed_contract_fields)
            ),
        })
        review["reasons"].append(
            "Outcome contract was changed after execution began"
        )
    else:
        review["checks"].append({
            "name": "contract-integrity",
            "passed": True,
            "notes": "Contract matches the snapshot captured at run creation",
        })

    # Check 0d: Access feasibility matches the claimed lifecycle state.
    access_feasibility_passed = True
    access_feasibility_notes = "Contract does not require build-time access discovery"
    if contract_type in ("build_capability", "connect_capability") and _source_system_requested(contract):
        operational_access = _has_operational_access_evidence(normalized_contract)
        provisioning_data = normalized_contract.get("provider_provisioning", {})
        provisioning_ready_for_access = bool(
            isinstance(provisioning_data, dict)
            and provisioning_data.get("status") in ("not_required", "ready")
            and provisioning_data.get("user_work_type") in ("none", "basic_consent")
        )
        if target_status in (
            "capability_ready_not_connected",
            "capability_connected",
        ):
            access_feasibility_passed = (
                operational_access and provisioning_ready_for_access
            )
            access_feasibility_notes = (
                "Authoritative and operational access evidence is present; "
                "provider provisioning is ready"
                if access_feasibility_passed
                else (
                    "Claimed ready/connected status lacks operational access "
                    "evidence or completed provider provisioning"
                )
            )
        elif target_status == "capability_built_access_blocked":
            access_feasibility_passed = not (
                operational_access and provisioning_ready_for_access
            )
            access_feasibility_notes = (
                "Access or provider-provisioning blockers are recorded truthfully"
                if access_feasibility_passed
                else "Access-blocked status has no unresolved access blocker"
            )

    review["checks"].append({
        "name": "access-feasibility",
        "passed": access_feasibility_passed,
        "notes": access_feasibility_notes,
    })
    if not access_feasibility_passed:
        review["reasons"].append(
            "Access feasibility does not support the claimed completion status"
        )

    # Check 0e: Ordinary work may not alter the framework that judges it.
    changed_paths = _changed_paths(
        project_root,
        run_data.get("framework_baseline_revision", ""),
    )
    protected_changes = [
        path for path in changed_paths if _is_protected_framework_path(path)
    ]
    if contract_type != "framework_change" and protected_changes:
        review["checks"].append({
            "name": "framework-integrity",
            "passed": False,
            "notes": (
                "Non-framework contract changed protected enforcement files: "
                + ", ".join(protected_changes)
            ),
        })
        review["reasons"].append(
            "Ordinary task modified completion gates, schemas, review rules, or agent protocol"
        )
    else:
        review["checks"].append({
            "name": "framework-integrity",
            "passed": True,
            "notes": (
                "Protected framework changes are covered by framework_change contract"
                if protected_changes
                else "No protected framework changes detected"
            ),
        })

    # Check 1: Outcome match - does delivery match contract?
    if contract_exists:
        expected_driver = contract.get("driver")
        actual_driver = run_data.get("driver")

        if actual_status != target_status:
            review["checks"].append({
                "name": "outcome-match",
                "passed": False,
                "notes": (
                    f"Run reports completion_status '{actual_status or 'missing'}'; "
                    f"contract targets '{target_status}'"
                ),
            })
            review["reasons"].append(
                "Run completion status does not match the reviewed contract target"
            )
        elif (
            contract_type != "framework_change"
            and expected_driver
            and actual_driver
            and expected_driver == actual_driver
        ):
            review["checks"].append({
                "name": "outcome-match",
                "passed": True,
                "notes": (
                    f"Driver '{actual_driver}' and completion status "
                    f"'{actual_status}' match contract"
                ),
            })
        elif contract_type == "framework_change":
            review["checks"].append({
                "name": "outcome-match",
                "passed": True,
                "notes": (
                    f"Framework change reports reviewed status '{actual_status}'"
                ),
            })
        elif expected_driver and not actual_driver:
            review["checks"].append({
                "name": "outcome-match",
                "passed": False,
                "notes": f"Contract specifies driver '{expected_driver}' but no driver recorded in run",
            })
            review["reasons"].append("No driver recorded - cannot verify outcome match")
        else:
            review["checks"].append({
                "name": "outcome-match",
                "passed": True,
                "notes": "Contract executed (driver check not applicable)",
            })
    else:
        review["checks"].append({
            "name": "outcome-match",
            "passed": False,
            "notes": "Cannot verify outcome match without contract file",
        })
        review["reasons"].append("Contract file missing")

    # Check 2: Naming honesty - do component names match what they do?
    # This checks if adapters exist and have appropriate trust status
    driver_name = run_data.get("driver")
    if contract_type == "framework_change":
        review["checks"].append({
            "name": "naming-honesty",
            "passed": True,
            "notes": "Framework changes do not require a workflow driver",
        })
    elif driver_name:
        driver_dir = project_root / "drivers" / driver_name
        driver_manifest = driver_dir / "manifest.yaml"
        if driver_manifest.exists():
            with open(driver_manifest) as f:
                driver_data = yaml.safe_load(f) or {}

            # Check adapter dependencies exist
            adapters = driver_data.get("depends_on", {}).get("adapters", [])
            if adapters:
                adapter_names = []
                for a in adapters:
                    if isinstance(a, str):
                        adapter_names.append(a)
                    elif isinstance(a, dict):
                        adapter_names.append(a.get("name", "unknown"))

                missing_adapters = []
                for adapter_name in adapter_names:
                    adapter_dir = project_root / "adapters" / adapter_name
                    if not adapter_dir.exists():
                        missing_adapters.append(adapter_name)

                if missing_adapters:
                    review["checks"].append({
                        "name": "naming-honesty",
                        "passed": False,
                        "notes": f"Missing adapters: {', '.join(missing_adapters)}",
                    })
                    review["reasons"].append(f"Adapters not found: {', '.join(missing_adapters)}")
                else:
                    review["checks"].append({
                        "name": "naming-honesty",
                        "passed": True,
                        "notes": f"All adapters exist: {', '.join(adapter_names)}",
                    })

                    if contract_exists:
                        raw_request = contract.get("raw_request", "")
                        manifest_text = _manifest_text(driver_manifest)
                        for adapter_name in adapter_names:
                            manifest_text += " "
                            manifest_text += _manifest_text(
                                project_root / "adapters" / adapter_name / "manifest.yaml"
                            )

                        if (
                            _source_system_requested(contract)
                            and _text_implies_fallback(manifest_text)
                            and not _request_explicitly_allows_fallback(raw_request)
                            and not _fallback_accepted(contract)
                        ):
                            # Override the earlier positive check with an explicit failure.
                            review["checks"][-1] = {
                                "name": "naming-honesty",
                                "passed": False,
                                "notes": (
                                    "Components for a source-system request expose "
                                    "fallback inputs instead of retrieving source data"
                                ),
                            }
                            review["reasons"].append(
                                "Component names/boundaries hide fallback input mode"
                            )
            else:
                review["checks"].append({
                    "name": "naming-honesty",
                    "passed": False,
                    "notes": "Driver has no adapter dependencies",
                })
                review["reasons"].append("Driver must depend on at least one adapter")
        else:
            review["checks"].append({
                "name": "naming-honesty",
                "passed": False,
                "notes": f"Driver manifest not found: {driver_name}",
            })
            review["reasons"].append(f"Driver '{driver_name}' not found")
    else:
        review["checks"].append({
            "name": "naming-honesty",
            "passed": False,
            "notes": "No driver specified in run",
        })
        review["reasons"].append("No driver in run data")

    # Check 3: User technical work - does user have to do technical tasks?
    user_work = run_data.get("requires_user_work", False)
    user_work_desc = run_data.get("user_work_description", "")
    provisioning = (
        normalized_contract.get("provider_provisioning", {})
        if contract_exists
        else {}
    )
    provisioning_user_work = (
        provisioning.get("user_work_type", "")
        if isinstance(provisioning, dict)
        else ""
    )
    access_blocked_build = (
        target_status == "capability_built_access_blocked"
    )

    if user_work or (
        provisioning_user_work in ("technical", "commercial_approval")
        and not access_blocked_build
    ):
        description = user_work_desc or (
            f"provider provisioning requires {provisioning_user_work}"
        )
        review["checks"].append({
            "name": "user-technical-work",
            "passed": False,
            "notes": f"User must perform: {description}",
        })
        review["reasons"].append(f"Requires user technical work: {description}")
    else:
        review["checks"].append({
            "name": "user-technical-work",
            "passed": True,
            "notes": (
                "Provider-side user work is recorded as an access blocker"
                if access_blocked_build
                and provisioning_user_work in ("technical", "commercial_approval")
                else "No user technical work required"
            ),
        })

    # Check 4: Capability lifecycle requirements.
    driver_data, adapter_manifests = _driver_components(project_root, driver_name)
    adapter_names = [name for name, _ in adapter_manifests]
    required_credentials = _required_credentials(adapter_manifests)
    has_external_adapter_read = any(
        _adapter_has_external_read(data) for _, data in adapter_manifests
    )
    driver_commands = _commands(driver_data)
    has_connection_command = bool(driver_commands & _CONNECTION_COMMANDS)
    connection = run_data.get("connection", {})
    connection_status = connection.get("status", "")
    credential_status = connection.get("credential_status", "")
    verification = run_data.get("verification", {})
    evidence = verification.get("evidence", {})
    if not isinstance(evidence, dict):
        evidence = {}
    has_operational_access = _has_operational_access_evidence(normalized_contract)
    provisioning_ready = bool(
        isinstance(provisioning, dict)
        and provisioning.get("status") in ("not_required", "ready")
        and provisioning_user_work in ("none", "basic_consent")
    )

    capability_passed = True
    capability_notes = "Contract type has no capability-build requirements"
    if contract_type == "build_capability":
        failures = []
        if not driver_data or not adapter_manifests:
            failures.append("driver and adapter manifests must exist")
        if _source_system_requested(contract) and not has_external_adapter_read:
            failures.append("adapter must declare a real external read operation")
        if required_credentials and not has_connection_command:
            failures.append(
                "driver must expose setup-auth, authorize, or connect command"
            )
        if _source_system_requested(contract) and target_status == "capability_built":
            failures.append(
                "source-system capability must use capability_ready_not_connected "
                "or capability_built_access_blocked"
            )
        if target_status == "capability_ready_not_connected":
            if not has_operational_access:
                failures.append(
                    "ready-not-connected requires authoritative and operational "
                    "access evidence"
                )
            if not provisioning_ready:
                failures.append(
                    "ready-not-connected requires completed provider provisioning "
                    "without technical user work"
                )
            if connection_status != "not_connected":
                failures.append("connection.status must be not_connected")
            if credential_status not in _MISSING_CREDENTIAL_STATUSES:
                failures.append(
                    "connection.credential_status must record missing or blocked credentials"
                )
        if target_status == "capability_built_access_blocked":
            if has_operational_access and provisioning_ready:
                failures.append(
                    "access-blocked status requires an unresolved access or "
                    "provider-provisioning blocker"
                )
            if connection_status != "not_connected":
                failures.append("access-blocked capability must remain not_connected")
        if required_credentials:
            authorization_mode = provisioning.get("authorization_mode", "none")
            required_behaviors = []
            if authorization_mode in ("secret_collection", "secret_and_browser"):
                required_behaviors.append(
                    ("setup-auth", "launches_secure_collection")
                )
            if authorization_mode in ("browser_oauth", "secret_and_browser"):
                required_behaviors.append(("authorize", "opens_browser"))
            required_behaviors.append(("connect", "validates_connection"))
            for command_name, behavior_name in required_behaviors:
                if not _behavior_verified(
                    driver_data,
                    evidence,
                    command_name,
                    behavior_name,
                ):
                    failures.append(
                        f"{command_name} must behaviorally verify default "
                        f"{behavior_name.replace('_', ' ')}"
                    )
            rollback_behaviors = []
            if provisioning.get("stores_local_credentials"):
                rollback_behaviors.append("removes_local_credentials")
            if provisioning.get("creates_external_grant"):
                rollback_behaviors.append("revokes_external_access")
            if rollback_behaviors and not any(
                _behavior_verified(
                    driver_data,
                    evidence,
                    "rollback",
                    behavior_name,
                )
                for behavior_name in rollback_behaviors
            ):
                failures.append(
                    "rollback must behaviorally verify credential removal or "
                    "external access revocation"
                )
        capability_passed = not failures
        capability_notes = (
            "Capability has a real access path, adapter/driver, auth command, and "
            f"truthful connection state; adapters: {', '.join(adapter_names)}"
            if capability_passed
            else "; ".join(failures)
        )
    elif contract_type == "connect_capability":
        failures = []
        if connection_status != "connected":
            failures.append("connection.status must be connected")
        if credential_status not in ("valid", "configured"):
            failures.append("connection.credential_status must be valid or configured")
        if not has_external_adapter_read:
            failures.append("connected capability must expose an external read operation")
        capability_passed = not failures
        capability_notes = (
            "Capability connection and credentials are verified"
            if capability_passed
            else "; ".join(failures)
        )

    review["checks"].append({
        "name": "capability-lifecycle",
        "passed": capability_passed,
        "notes": capability_notes,
    })
    if not capability_passed:
        review["reasons"].append(
            "Capability lifecycle failed: " + capability_notes
        )

    # Check 5: The user-facing claim may not overstate the terminal state.
    user_facing_status = run_data.get("user_facing_status")
    claim_passed = bool(
        actual_status and user_facing_status and actual_status == user_facing_status
    )
    review["checks"].append({
        "name": "completion-claim",
        "passed": claim_passed,
        "notes": (
            f"User-facing status truthfully reports '{actual_status}'"
            if claim_passed
            else (
                f"user_facing_status '{user_facing_status or 'missing'}' must equal "
                f"completion_status '{actual_status or 'missing'}'"
            )
        ),
    })
    if not claim_passed:
        review["reasons"].append(
            "User-facing completion claim is missing or overstates delivery"
        )

    # Check 6: Verification authenticity - was the required real system used?
    verification_status = verification.get("status", "not_verified")
    raw_request = contract.get("raw_request", "") if contract_exists else ""
    source_system_request = (
        _source_system_requested(contract)
        and not _request_explicitly_allows_fallback(raw_request)
        and not _fallback_accepted(contract)
    )
    effects = run_data.get("effects", [])
    has_external_read = any(
        isinstance(effect, dict)
        and effect.get("risk") == "read"
        and effect.get("scope") in ("external", "production")
        for effect in effects
    )

    requires_live_source_evidence = (
        contract_type in ("connect_capability", "execute_workflow")
        and source_system_request
    )

    if verification_status == "verified":
        if requires_live_source_evidence and not has_external_read:
            review["checks"].append({
                "name": "verification-authenticity",
                "passed": False,
                "notes": (
                    f"{contract_type} requires live source-system evidence, but "
                    "run effects show no external read from that source"
                ),
            })
            review["reasons"].append(
                "Verification did not prove source-system retrieval"
            )
        elif (
            contract_type == "build_capability"
            and target_status == "capability_ready_not_connected"
            and evidence
        ):
            review["checks"].append({
                "name": "verification-authenticity",
                "passed": True,
                "notes": (
                    "Build evidence is present; live source access is correctly "
                    "deferred until credentials are connected"
                ),
            })
        elif evidence:
            review["checks"].append({
                "name": "verification-authenticity",
                "passed": True,
                "notes": "Verification evidence present",
            })
        else:
            review["checks"].append({
                "name": "verification-authenticity",
                "passed": False,
                "notes": "Verified status but no evidence captured",
            })
            review["reasons"].append("No verification evidence")
    else:
        review["checks"].append({
            "name": "verification-authenticity",
            "passed": False,
            "notes": f"Verification status: {verification_status}",
        })
        review["reasons"].append(f"Verification not complete: {verification_status}")

    # Determine overall status
    all_passed = all(c.get("passed", False) for c in review["checks"])
    review["status"] = "approved" if all_passed else "rejected"

    return review


def complete_run(
    run_id: str,
    project_root: Optional[str | Path] = None,
    force: bool = False,
) -> CompletionResult:
    """
    Complete a workflow run, enforcing all gates.

    This is the ONLY valid way to complete a PocketOps workflow.
    It enforces all VERIFY → COMPLETE gates and records the completion.

    Review is ALWAYS mandatory. There is no skip option.

    Args:
        run_id: ID of the run to complete
        project_root: Path to project root (auto-detected if not provided)
        force: Deprecated. Gate overrides are prohibited.

    Returns:
        CompletionResult with success status and details

    Raises:
        CompletionError: If completion is blocked and force=False
    """
    project_root = Path(project_root) if project_root else _find_project_root()
    runs_dir = project_root / "runs" / "current"
    archive_dir = project_root / "runs" / "archive"

    if force:
        raise CompletionError(
            gate_name="gate-integrity",
            message=(
                "force completion is disabled. Fix the rejected contract, review, "
                "or evidence instead of weakening completion gates."
            ),
        )

    # Load run file
    run_file, run_data = _load_run_file(runs_dir, run_id)

    # Always regenerate review. A prewritten approval is not trusted evidence.
    review = _run_reviewing_contracts(run_data, project_root)
    run_data["review"] = review

    with open(run_file, "w") as f:
        yaml.safe_dump(run_data, f, default_flow_style=False, sort_keys=False)

    # Build context for gate checks
    context = {
        "run_id": run_id,
        "project_root": str(project_root),
    }

    # Check all VERIFY → COMPLETE gates
    can_complete, gate_results = GateRegistry.can_transition(
        Phase.VERIFY,
        Phase.COMPLETE,
        context,
    )

    failed_gates = [r for r in gate_results if not r.passed]

    if not can_complete:
        # Find the first blocking gate
        first_failure = failed_gates[0] if failed_gates else None
        raise CompletionError(
            gate_name=first_failure.gate_name if first_failure is not None else "unknown",
            message=first_failure.message if first_failure is not None else "Gate check failed",
            details={
                "gate_results": [
                    {"gate": r.gate_name, "passed": r.passed, "message": r.message}
                    for r in gate_results
                ],
            },
        )

    # Record completion
    run_data["status"] = "complete"
    run_data["completed_at"] = datetime.now().isoformat()
    run_data["completion"] = {
        "method": "pocketops.workflow.complete_run",
        "gates_passed": can_complete,
        "forced": False,
        "gate_results": [
            {"gate": r.gate_name, "passed": r.passed, "message": r.message}
            for r in gate_results
        ],
    }

    # Save updated run file
    with open(run_file, "w") as f:
        yaml.safe_dump(run_data, f, default_flow_style=False, sort_keys=False)

    # Archive the run
    archive_subdir = archive_dir / datetime.now().strftime("%Y-%m-%d")
    archive_subdir.mkdir(parents=True, exist_ok=True)
    archived_path = archive_subdir / run_file.name

    # Move to archive
    run_file.rename(archived_path)

    return CompletionResult(
        success=True,
        run_id=run_id,
        message=(
            f"Run completed successfully with status "
            f"'{run_data.get('completion_status')}'"
        ),
        gate_results=gate_results,
        archived_to=str(archived_path),
    )


def check_completion_ready(
    run_id: str,
    project_root: Optional[str | Path] = None,
) -> tuple[bool, list[GateResult]]:
    """
    Check if a run is ready for completion (without completing it).

    Returns:
        (ready, gate_results)
    """
    project_root = Path(project_root) if project_root else _find_project_root()
    runs_dir = project_root / "runs" / "current"

    # Validate that the run exists before checking transition gates.
    _load_run_file(runs_dir, run_id)

    # Build context
    context = {
        "run_id": run_id,
        "project_root": str(project_root),
    }

    # Check gates
    return GateRegistry.can_transition(Phase.VERIFY, Phase.COMPLETE, context)
