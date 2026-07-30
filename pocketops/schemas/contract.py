"""
Outcome contract schema.

Contracts define what success looks like BEFORE execution begins.
They are the foundation of the VERIFY → COMPLETE gate.
"""

from typing import Optional
from pydantic import BaseModel, model_validator
from datetime import datetime


class VerificationCheck(BaseModel):
    """A single verification check to confirm outcome."""
    name: str
    description: str
    method: str  # e.g., "retrieve-and-compare", "count-and-match", "state-transition"
    expected: Optional[str] = None
    critical: bool = True  # If false, partial success is acceptable


class Verification(BaseModel):
    """Verification specification for a contract."""
    checks: list[VerificationCheck] = []
    evidence_required: bool = True


class Constraint(BaseModel):
    """A constraint on how the outcome should be achieved."""
    name: str
    description: str


class OutcomeContract(BaseModel):
    """
    Outcome contract defining success criteria.

    Contracts are created during PLAN phase and must exist before BUILD.
    They define:
    - What the user actually wants (outcome)
    - How we'll verify it was achieved (verification)
    - What constraints must be respected (constraints)
    """
    id: str
    created_at: str
    outcome: str  # Plain language description of desired outcome
    verification: Verification
    constraints: list[Constraint] = []
    user_technical_work: bool = False  # True if user must do technical work (FAIL)
    driver: Optional[str] = None  # Which driver will be used
    status: str = "draft"  # draft, approved, executing, verified, complete

    @model_validator(mode="after")
    def validate_has_verification(self):
        """Contracts must specify how to verify the outcome."""
        if not self.verification.checks:
            raise ValueError(
                "Contract must specify at least one verification check. "
                "Without verification, we can't confirm the outcome was achieved."
            )
        return self

    @model_validator(mode="after")
    def validate_no_user_technical_work(self):
        """
        Flag contracts that require user to do technical work.

        This doesn't fail validation but surfaces it for review.
        The reviewing-contracts skill should reject these.
        """
        # We don't fail here - let the review skill catch this
        return self

    @classmethod
    def create(
        cls,
        outcome: str,
        checks: list[dict],
        constraints: list[dict] | None = None,
        driver: str | None = None,
    ) -> "OutcomeContract":
        """Factory method to create a new contract."""
        import uuid

        verification_checks = [
            VerificationCheck(**check) for check in checks
        ]

        constraint_list = [
            Constraint(**c) for c in (constraints or [])
        ]

        return cls(
            id=str(uuid.uuid4())[:8],
            created_at=datetime.now().isoformat(),
            outcome=outcome,
            verification=Verification(checks=verification_checks),
            constraints=constraint_list,
            driver=driver,
        )
