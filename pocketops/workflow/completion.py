"""
Workflow completion enforcement.

This module provides the ONLY valid way to complete a PocketOps workflow.
The complete_run() function enforces ALL gates and blocks completion if any fail.

IMPORTANT: Agents declaring "done" without calling complete_run() have NOT
actually completed the workflow. The run record will show incomplete status.
"""

import os
import yaml
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional

from pocketops.gates import Phase, GateRegistry, GateResult


class CompletionError(Exception):
    """Raised when completion is blocked by a gate."""

    def __init__(self, gate_name: str, message: str, details: dict = None):
        self.gate_name = gate_name
        self.message = message
        self.details = details or {}
        super().__init__(f"Completion blocked by {gate_name}: {message}")


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

    # Check 1: Outcome match - does delivery match contract?
    contract_id = run_data.get("contract_id") or run_data.get("plan", {}).get("contract_id")
    if contract_id:
        plans_dir = project_root / "plans" / "active"
        contract_file = plans_dir / f"{contract_id}.yaml"
        if contract_file.exists():
            with open(contract_file) as f:
                contract = yaml.safe_load(f) or {}

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
                "notes": f"Contract file not found: {contract_id}",
            })
            review["reasons"].append("Contract file missing")
    else:
        review["checks"].append({
            "name": "outcome-match",
            "passed": False,
            "notes": "No contract_id in run data",
        })
        review["reasons"].append("No contract reference in run")

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

    if verification_status == "verified":
        evidence = verification.get("evidence", {})
        if evidence:
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
    skip_review: bool = False,
    force: bool = False,
) -> CompletionResult:
    """
    Complete a workflow run, enforcing all gates.

    This is the ONLY valid way to complete a PocketOps workflow.
    It enforces all VERIFY → COMPLETE gates and records the completion.

    Args:
        run_id: ID of the run to complete
        project_root: Path to project root (auto-detected if not provided)
        skip_review: Skip review for low-risk operations (blocked for high-risk)
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
        "skip_review": skip_review,
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
            gate_name=first_failure.gate_name if first_failure else "unknown",
            message=first_failure.message if first_failure else "Gate check failed",
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
