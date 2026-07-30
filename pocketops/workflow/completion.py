"""
Workflow completion enforcement.

This module provides the ONLY valid way to start and complete a PocketOps workflow.

- create_run() MUST be called before execution starts
- complete_run() MUST be called to finish (enforces all gates)

IMPORTANT: Agents declaring "done" without calling complete_run() have NOT
actually completed the workflow. The run record will show incomplete status.
"""

import os
import yaml
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, List

from pocketops.gates import Phase, GateRegistry, GateResult

# Import gate implementations so decorators register checks before transitions.
import pocketops.gates.checks  # noqa: F401


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


class RunCreationError(Exception):
    """Raised when run creation fails."""

    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


class CompletionError(Exception):
    """Raised when completion is blocked by a gate."""

    def __init__(self, gate_name: str, message: str, details: dict = None):
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
    driver: str
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


def create_run(
    contract_id: str,
    driver: str,
    effects: List[dict] = None,
    inputs: dict = None,
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

        load_contract(contract_file)
    except Exception as e:
        raise RunCreationError(
            f"Contract '{contract_id}' is invalid. Fix the outcome contract before execution.",
            details={"contract_id": contract_id, "contract_file": str(contract_file), "error": str(e)},
        ) from e

    # Validate driver exists
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
    run_id = f"{timestamp}-{driver}"

    # Create run record
    run_data = {
        "run_id": run_id,
        "contract_id": contract_id,
        "driver": driver,
        "status": "created",
        "created_at": datetime.now().isoformat(),
        "inputs": inputs or {},
        "effects": effects or [],
        "outputs": {},
        "verification": {
            "status": "not_verified",
            "checks": [],
            "evidence": {},
        },
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
    plan_file_path = run_data.get("plan_file") or run_data.get("plan", {}).get("file")

    plans_dir = project_root / "plans" / "active"
    contract_exists = False
    contract = {}

    if contract_id:
        contract_file = plans_dir / f"{contract_id}.yaml"
        if not contract_file.exists():
            contract_file = plans_dir / f"{contract_id}.yml"

        if contract_file.exists():
            contract_exists = True
            with open(contract_file) as f:
                contract = yaml.safe_load(f) or {}
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

    # Check 1: Outcome match - does delivery match contract?
    if contract_exists:
        # Check if driver was specified and used
        expected_driver = contract.get("driver")
        actual_driver = run_data.get("driver")

        if expected_driver and actual_driver and expected_driver == actual_driver:
            review["checks"].append({
                "name": "outcome-match",
                "passed": True,
                "notes": f"Driver '{actual_driver}' matches contract",
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
    if driver_name:
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

    if user_work:
        review["checks"].append({
            "name": "user-technical-work",
            "passed": False,
            "notes": f"User must perform: {user_work_desc}",
        })
        review["reasons"].append(f"Requires user technical work: {user_work_desc}")
    else:
        review["checks"].append({
            "name": "user-technical-work",
            "passed": True,
            "notes": "No user technical work required",
        })

    # Check 4: Verification authenticity - was real system used?
    verification = run_data.get("verification", {})
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

    if verification_status == "verified":
        evidence = verification.get("evidence", {})
        if source_system_request and not has_external_read:
            review["checks"].append({
                "name": "verification-authenticity",
                "passed": False,
                "notes": (
                    "Raw request requires source-system data, but run effects "
                    "show no external read from that source"
                ),
            })
            review["reasons"].append(
                "Verification did not prove source-system retrieval"
            )
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
        force: Force completion even if gates fail (records override reason)

    Returns:
        CompletionResult with success status and details

    Raises:
        CompletionError: If completion is blocked and force=False
    """
    project_root = Path(project_root) if project_root else _find_project_root()
    runs_dir = project_root / "runs" / "current"
    archive_dir = project_root / "runs" / "archive"

    # Load run file
    run_file, run_data = _load_run_file(runs_dir, run_id)

    # Run the reviewing-contracts checks and record them
    if "review" not in run_data or run_data.get("review", {}).get("status") == "pending":
        review = _run_reviewing_contracts(run_data, project_root)
        run_data["review"] = review

        # Save updated run file with review
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

    if not can_complete and not force:
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
        "forced": force and not can_complete,
        "gate_results": [
            {"gate": r.gate_name, "passed": r.passed, "message": r.message}
            for r in gate_results
        ],
    }

    if force and not can_complete:
        run_data["completion"]["force_reason"] = "Operator override"
        run_data["completion"]["failed_gates"] = [
            {"gate": r.gate_name, "message": r.message}
            for r in failed_gates
        ]

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
        message="Run completed successfully" if can_complete else "Run completed with force override",
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

    # Load run file
    run_file, run_data = _load_run_file(runs_dir, run_id)

    # Build context
    context = {
        "run_id": run_id,
        "project_root": str(project_root),
    }

    # Check gates
    return GateRegistry.can_transition(Phase.VERIFY, Phase.COMPLETE, context)
