"""
Gate check implementations.

These are the actual gate functions that enforce constraints
at phase transitions.
"""

import os
from pathlib import Path
from typing import Optional

from pocketops.gates.registry import GateRegistry, GateResult, Phase


def _find_project_root() -> Path:
    """Find the PocketOps project root."""
    # Start from current working directory
    cwd = Path.cwd()

    # Look for PocketOps markers
    markers = ["plans", "runs", "adapters", "drivers", "transports"]

    current = cwd
    while current != current.parent:
        if all((current / m).exists() for m in ["plans", "runs"]):
            return current
        current = current.parent

    # Fallback to cwd
    return cwd


@GateRegistry.register(
    name="contract-required",
    from_phase=Phase.PLAN,
    to_phase=Phase.BUILD,
    description="Outcome contract must exist in plans/active/ before building",
)
def check_contract_exists(context: dict) -> GateResult:
    """
    Verify an outcome contract exists before allowing BUILD phase.

    Context should contain:
        - contract_id: ID of the contract to check
        - project_root: Optional path to project root
    """
    contract_id = context.get("contract_id")
    project_root = Path(context.get("project_root", _find_project_root()))
    plans_dir = project_root / "plans" / "active"

    if not contract_id:
        # Check if any contract exists
        if not plans_dir.exists():
            return GateResult(
                passed=False,
                gate_name="contract-required",
                message="No plans/active directory found",
            )

        contracts = list(plans_dir.glob("*.yaml")) + list(plans_dir.glob("*.yml"))
        if not contracts:
            return GateResult(
                passed=False,
                gate_name="contract-required",
                message="No outcome contract found in plans/active/. "
                        "Create a contract defining what success looks like before building.",
            )

        return GateResult(
            passed=True,
            gate_name="contract-required",
            message=f"Found {len(contracts)} contract(s) in plans/active/",
            details={"contracts": [str(c) for c in contracts]},
        )

    # Check for specific contract
    contract_path = plans_dir / f"{contract_id}.yaml"
    if not contract_path.exists():
        contract_path = plans_dir / f"{contract_id}.yml"

    if not contract_path.exists():
        return GateResult(
            passed=False,
            gate_name="contract-required",
            message=f"Contract '{contract_id}' not found in plans/active/",
        )

    return GateResult(
        passed=True,
        gate_name="contract-required",
        message=f"Contract '{contract_id}' found",
        details={"path": str(contract_path)},
    )


@GateRegistry.register(
    name="dry-run-required",
    from_phase=Phase.DRY_RUN,
    to_phase=Phase.APPROVE,
    description="Successful dry-run must complete before approval",
)
def check_dry_run_completed(context: dict) -> GateResult:
    """
    Verify a dry-run was completed before allowing APPROVE phase.

    Context should contain:
        - run_id: ID of the current run
        - project_root: Optional path to project root
    """
    run_id = context.get("run_id")
    project_root = Path(context.get("project_root", _find_project_root()))
    runs_dir = project_root / "runs" / "current"

    if not run_id:
        return GateResult(
            passed=False,
            gate_name="dry-run-required",
            message="No run_id provided in context",
        )

    # Look for dry-run record
    dry_run_file = runs_dir / f"{run_id}-dry-run.yaml"
    if not dry_run_file.exists():
        dry_run_file = runs_dir / f"{run_id}-dry-run.yml"

    if not dry_run_file.exists():
        # Also check for a dry_run field in the main run file
        run_file = runs_dir / f"{run_id}.yaml"
        if run_file.exists():
            import yaml
            with open(run_file) as f:
                run_data = yaml.safe_load(f)
            if run_data and run_data.get("dry_run", {}).get("completed"):
                return GateResult(
                    passed=True,
                    gate_name="dry-run-required",
                    message="Dry-run completed (recorded in run file)",
                    details={"run_file": str(run_file)},
                )

        return GateResult(
            passed=False,
            gate_name="dry-run-required",
            message=f"No dry-run record found for run '{run_id}'. "
                    "Execute a dry-run before requesting approval.",
        )

    # Verify dry-run succeeded
    import yaml
    with open(dry_run_file) as f:
        dry_run_data = yaml.safe_load(f)

    if not dry_run_data:
        return GateResult(
            passed=False,
            gate_name="dry-run-required",
            message="Dry-run file is empty",
        )

    status = dry_run_data.get("status", "unknown")
    if status not in ("success", "passed", "complete"):
        return GateResult(
            passed=False,
            gate_name="dry-run-required",
            message=f"Dry-run status is '{status}', not 'success'",
            details={"dry_run_data": dry_run_data},
        )

    return GateResult(
        passed=True,
        gate_name="dry-run-required",
        message="Dry-run completed successfully",
        details={"path": str(dry_run_file)},
    )


@GateRegistry.register(
    name="verification-required",
    from_phase=Phase.VERIFY,
    to_phase=Phase.COMPLETE,
    description="Verification must pass before marking complete",
)
def check_verification_passed(context: dict) -> GateResult:
    """
    Verify the outcome was verified before allowing COMPLETE phase.

    Context should contain:
        - run_id: ID of the current run
        - project_root: Optional path to project root
    """
    run_id = context.get("run_id")
    project_root = Path(context.get("project_root", _find_project_root()))
    runs_dir = project_root / "runs" / "current"

    if not run_id:
        return GateResult(
            passed=False,
            gate_name="verification-required",
            message="No run_id provided in context",
        )

    # Look for verification in run file
    run_file = runs_dir / f"{run_id}.yaml"
    if not run_file.exists():
        run_file = runs_dir / f"{run_id}.yml"

    if not run_file.exists():
        return GateResult(
            passed=False,
            gate_name="verification-required",
            message=f"Run file not found for '{run_id}'",
        )

    import yaml
    with open(run_file) as f:
        run_data = yaml.safe_load(f)

    if not run_data:
        return GateResult(
            passed=False,
            gate_name="verification-required",
            message="Run file is empty",
        )

    verification = run_data.get("verification", {})
    status = verification.get("status", "not_verified")

    if status == "verified":
        return GateResult(
            passed=True,
            gate_name="verification-required",
            message="Outcome verified successfully",
            details={"verification": verification},
        )

    if status == "partial":
        return GateResult(
            passed=False,
            gate_name="verification-required",
            message="Verification is partial - some checks failed. "
                    "Resolve issues before completing.",
            details={"verification": verification},
        )

    return GateResult(
        passed=False,
        gate_name="verification-required",
        message=f"Verification status is '{status}'. "
                "Run verification checks before completing.",
        details={"verification": verification},
    )


@GateRegistry.register(
    name="review-required",
    from_phase=Phase.VERIFY,
    to_phase=Phase.COMPLETE,
    description="Contract review must approve before completion",
)
def check_review_approved(context: dict) -> GateResult:
    """
    Verify contract review was approved before allowing COMPLETE phase.

    This is an optional gate - if no review is required, it passes.

    Context should contain:
        - run_id: ID of the current run
        - require_review: Whether review is mandatory (default: False)
        - project_root: Optional path to project root
    """
    require_review = context.get("require_review", False)

    if not require_review:
        return GateResult(
            passed=True,
            gate_name="review-required",
            message="Review not required for this run",
        )

    run_id = context.get("run_id")
    project_root = Path(context.get("project_root", _find_project_root()))
    runs_dir = project_root / "runs" / "current"

    if not run_id:
        return GateResult(
            passed=False,
            gate_name="review-required",
            message="No run_id provided in context",
        )

    # Look for review in run file
    run_file = runs_dir / f"{run_id}.yaml"
    if not run_file.exists():
        run_file = runs_dir / f"{run_id}.yml"

    if not run_file.exists():
        return GateResult(
            passed=False,
            gate_name="review-required",
            message=f"Run file not found for '{run_id}'",
        )

    import yaml
    with open(run_file) as f:
        run_data = yaml.safe_load(f)

    if not run_data:
        return GateResult(
            passed=False,
            gate_name="review-required",
            message="Run file is empty",
        )

    review = run_data.get("review", {})
    status = review.get("status", "not_reviewed")

    if status == "approved":
        return GateResult(
            passed=True,
            gate_name="review-required",
            message="Contract review approved",
            details={"review": review},
        )

    if status == "rejected":
        reasons = review.get("reasons", [])
        return GateResult(
            passed=False,
            gate_name="review-required",
            message=f"Contract review rejected: {', '.join(reasons)}",
            details={"review": review},
        )

    return GateResult(
        passed=False,
        gate_name="review-required",
        message="Contract review required but not completed",
        details={"review": review},
    )
