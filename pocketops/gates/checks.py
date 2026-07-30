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


def _validate_contract_content(contract_path: Path) -> tuple[bool, str, dict]:
    """
    Validate contract file content against OutcomeContract schema.

    Returns:
        (valid, message, contract_data or error_details)
    """
    import yaml
    from pydantic import ValidationError

    try:
        with open(contract_path) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return False, f"Invalid YAML: {e}", {}

    if not data:
        return False, "Contract file is empty", {}

    # Import here to avoid circular dependency
    from pocketops.schemas import OutcomeContract

    try:
        contract = OutcomeContract(**data)
        return True, "Contract is valid", {
            "id": contract.id,
            "outcome": contract.outcome,
            "verification_checks": len(contract.verification.checks),
            "driver": contract.driver,
        }
    except ValidationError as e:
        details = []
        for error in e.errors():
            loc = ".".join(str(l) for l in error["loc"])
            details.append(f"{loc}: {error['msg']}")
        return False, "Contract validation failed: " + "; ".join(details), {}


@GateRegistry.register(
    name="contract-required",
    from_phase=Phase.PLAN,
    to_phase=Phase.BUILD,
    description="Valid outcome contract must exist in plans/active/ before building",
)
def check_contract_exists(context: dict) -> GateResult:
    """
    Verify a VALID outcome contract exists before allowing BUILD phase.

    This gate validates:
    1. Contract file exists
    2. Contract is valid YAML
    3. Contract passes OutcomeContract schema validation
    4. Contract has at least one verification check

    Context should contain:
        - contract_id: ID of the contract to check (optional)
        - project_root: Optional path to project root
    """
    contract_id = context.get("contract_id")
    project_root = Path(context.get("project_root", _find_project_root()))
    plans_dir = project_root / "plans" / "active"

    if not plans_dir.exists():
        return GateResult(
            passed=False,
            gate_name="contract-required",
            message="No plans/active directory found",
        )

    if not contract_id:
        # Check if any valid contract exists
        contracts = list(plans_dir.glob("*.yaml")) + list(plans_dir.glob("*.yml"))
        if not contracts:
            return GateResult(
                passed=False,
                gate_name="contract-required",
                message="No outcome contract found in plans/active/. "
                        "Create a contract defining what success looks like before building.",
            )

        # Validate at least one contract is structurally valid
        valid_contracts = []
        invalid_contracts = []

        for contract_path in contracts:
            valid, message, details = _validate_contract_content(contract_path)
            if valid:
                valid_contracts.append({
                    "path": str(contract_path),
                    **details
                })
            else:
                invalid_contracts.append({
                    "path": str(contract_path),
                    "error": message
                })

        if not valid_contracts:
            return GateResult(
                passed=False,
                gate_name="contract-required",
                message=f"Found {len(contracts)} contract file(s) but none are valid. "
                        "Contracts must have outcome, id, and verification checks.",
                details={"invalid_contracts": invalid_contracts},
            )

        return GateResult(
            passed=True,
            gate_name="contract-required",
            message=f"Found {len(valid_contracts)} valid contract(s)",
            details={
                "valid_contracts": valid_contracts,
                "invalid_contracts": invalid_contracts if invalid_contracts else None,
            },
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

    # Validate the specific contract
    valid, message, details = _validate_contract_content(contract_path)

    if not valid:
        return GateResult(
            passed=False,
            gate_name="contract-required",
            message=f"Contract '{contract_id}' exists but is invalid: {message}",
            details={"path": str(contract_path)},
        )

    return GateResult(
        passed=True,
        gate_name="contract-required",
        message=f"Contract '{contract_id}' is valid",
        details={"path": str(contract_path), **details},
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


def _is_high_risk_run(run_data: dict) -> bool:
    """
    Determine if a run is high-risk and requires mandatory review.

    High-risk operations include:
    - External writes (scope: external)
    - Destructive operations (risk: destructive)
    - Batch operations affecting multiple records
    """
    effects = run_data.get("effects", [])
    for effect in effects:
        risk = effect.get("risk", "").lower()
        scope = effect.get("scope", "").lower()

        if risk in ("destructive", "write", "high", "critical"):
            return True
        if scope in ("external", "batch", "destructive"):
            return True

    # Check driver info if available
    driver_info = run_data.get("driver_info", {})
    if driver_info.get("risk", "").lower() in ("high", "critical", "destructive"):
        return True

    return False


def _validate_review_checks(review: dict) -> tuple[bool, list[str]]:
    """
    Validate that all review checks passed, not just the status field.

    Returns:
        (all_passed, list of failed check names)
    """
    checks = review.get("checks", [])
    if not checks:
        # No checks recorded - can't validate
        return False, ["No review checks recorded"]

    failed_checks = []
    for check in checks:
        check_name = check.get("name", "unknown")
        passed = check.get("passed", False)
        if not passed:
            failed_checks.append(check_name)

    return len(failed_checks) == 0, failed_checks


@GateRegistry.register(
    name="review-required",
    from_phase=Phase.VERIFY,
    to_phase=Phase.COMPLETE,
    description="Contract review must approve before completion",
)
def check_review_approved(context: dict) -> GateResult:
    """
    Verify contract review was approved before allowing COMPLETE phase.

    Review is MANDATORY for high-risk operations (external writes, destructive ops).
    Review can be skipped for low-risk read-only operations.

    This gate validates BOTH:
    1. Review status is "approved"
    2. All individual review checks passed (outcome-match, naming-honesty, etc.)

    Context should contain:
        - run_id: ID of the current run
        - skip_review: Explicit opt-out (only works for low-risk runs)
        - project_root: Optional path to project root
    """
    run_id = context.get("run_id")
    skip_review = context.get("skip_review", False)
    project_root = Path(context.get("project_root", _find_project_root()))
    runs_dir = project_root / "runs" / "current"

    if not run_id:
        return GateResult(
            passed=False,
            gate_name="review-required",
            message="No run_id provided in context",
        )

    # Look for run file
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

    # Check if this is a high-risk run
    is_high_risk = _is_high_risk_run(run_data)

    # High-risk runs ALWAYS require review
    if is_high_risk and skip_review:
        return GateResult(
            passed=False,
            gate_name="review-required",
            message="Cannot skip review for high-risk operations. "
                    "Run reviewing-contracts skill before completion.",
            details={"high_risk": True, "effects": run_data.get("effects", [])},
        )

    # Low-risk runs can opt out
    if skip_review and not is_high_risk:
        return GateResult(
            passed=True,
            gate_name="review-required",
            message="Review skipped (low-risk operation)",
            details={"high_risk": False},
        )

    # Check for review in run file
    review = run_data.get("review", {})
    status = review.get("status", "not_reviewed")

    if status == "not_reviewed" or not review:
        if is_high_risk:
            return GateResult(
                passed=False,
                gate_name="review-required",
                message="Contract review required for high-risk operation. "
                        "Run reviewing-contracts skill before completion.",
                details={"high_risk": True},
            )
        else:
            return GateResult(
                passed=False,
                gate_name="review-required",
                message="Contract review not completed. "
                        "Run reviewing-contracts skill or set skip_review=True for low-risk ops.",
            )

    if status == "rejected":
        reasons = review.get("reasons", [])
        return GateResult(
            passed=False,
            gate_name="review-required",
            message=f"Contract review rejected: {', '.join(reasons)}",
            details={"review": review},
        )

    if status == "approved":
        # Validate that all checks actually passed
        checks_valid, failed_checks = _validate_review_checks(review)

        if not checks_valid:
            return GateResult(
                passed=False,
                gate_name="review-required",
                message=f"Review status is 'approved' but checks failed: {', '.join(failed_checks)}. "
                        "Review must have all checks passing to be valid.",
                details={"review": review, "failed_checks": failed_checks},
            )

        return GateResult(
            passed=True,
            gate_name="review-required",
            message="Contract review approved with all checks passing",
            details={"review": review},
        )

    return GateResult(
        passed=False,
        gate_name="review-required",
        message=f"Unknown review status: {status}",
        details={"review": review},
    )
