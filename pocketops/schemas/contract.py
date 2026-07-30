"""
Outcome contract schema.

Contracts define what success looks like BEFORE execution begins.
They are the foundation of the VERIFY → COMPLETE gate.
"""

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field, model_validator
from datetime import datetime


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

_ACCESS_DISCOVERY_FIELDS = (
    "official_api",
    "sdk_or_cli",
    "delegated_provider",
    "browser_flow",
    "credential_flow",
)

_NON_VIABLE_ACCESS_STATUSES = (
    "blocked",
    "unavailable",
    "not available",
    "not checked",
    "unchecked",
    "checked",
    "attempted",
    "none",
    "n/a",
    "unknown",
)

_FRAMEWORK_CHANGE_TERMS = (
    "pocketops",
    "framework",
    "completion gate",
    "completion gates",
    "gate enforcement",
    "contract schema",
    "review skill",
    "review protocol",
    "architecture",
    "protocol",
    "harden",
)


class ContractType(str, Enum):
    """Execution contract categories with distinct completion rules."""

    BUILD_CAPABILITY = "build_capability"
    CONNECT_CAPABILITY = "connect_capability"
    EXECUTE_WORKFLOW = "execute_workflow"
    FRAMEWORK_CHANGE = "framework_change"


class CompletionStatus(str, Enum):
    """Truthful terminal states a run may report."""

    CAPABILITY_BUILT = "capability_built"
    CAPABILITY_READY_NOT_CONNECTED = "capability_ready_not_connected"
    CAPABILITY_CONNECTED = "capability_connected"
    OUTCOME_DELIVERED = "outcome_delivered"


def _normalize(value: str | None) -> str:
    return (value or "").lower()


def _contains_any(value: str, terms: tuple[str, ...]) -> bool:
    return any(term in value for term in terms)


def _request_implies_source_system_access(raw_request: str) -> bool:
    normalized = _normalize(raw_request)
    return _contains_any(normalized, _SOURCE_SYSTEM_REQUEST_TERMS)


def _request_explicitly_allows_fallback(raw_request: str) -> bool:
    normalized = _normalize(raw_request)
    return _contains_any(normalized, _FALLBACK_TERMS)


def _contract_uses_fallback(text: str) -> bool:
    normalized = _normalize(text)
    return _contains_any(normalized, _FALLBACK_TERMS)


def _request_implies_framework_change(raw_request: str) -> bool:
    return _contains_any(_normalize(raw_request), _FRAMEWORK_CHANGE_TERMS)


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


class AccessDiscovery(BaseModel):
    """
    Records source-system access paths checked before choosing a fallback.

    Values are free-form short statuses such as "available", "unavailable",
    "blocked", or "needs-credentials" because every system has different
    discovery surfaces.
    """
    official_api: Optional[str] = None
    sdk_or_cli: Optional[str] = None
    delegated_provider: Optional[str] = None
    browser_flow: Optional[str] = None
    credential_flow: Optional[str] = None
    notes: Optional[str] = None

    def has_attempted_access_path(self) -> bool:
        return any(getattr(self, field) for field in _ACCESS_DISCOVERY_FIELDS)

    def has_viable_access_path(self) -> bool:
        """Return true when discovery found or planned a usable access route."""
        for field in _ACCESS_DISCOVERY_FIELDS:
            status = _normalize(getattr(self, field))
            if status and not _contains_any(status, _NON_VIABLE_ACCESS_STATUSES):
                return True
        return False


class SourceSystemRequest(BaseModel):
    """Declares that the user requested data/action from an external source system."""
    requested: bool = False
    system: Optional[str] = None
    expected_agent_access: bool = True


class FallbackMode(BaseModel):
    """Declares that delivery uses a reduced-scope fallback instead of source access."""
    type: Optional[str] = None  # manual_file, user_copy_paste, mock_data, sandbox_only, other
    explicitly_requested_by_user: bool = False
    accepted_after_access_discovery: bool = False
    reason: Optional[str] = None

    @property
    def active(self) -> bool:
        return bool(self.type)


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
    raw_request: str
    contract_type: ContractType
    target_completion_status: CompletionStatus
    outcome: str  # Plain language description of desired outcome
    verification: Verification
    constraints: list[Constraint] = []
    source_system_request: SourceSystemRequest = Field(default_factory=SourceSystemRequest)
    access_discovery: Optional[AccessDiscovery] = None
    fallback_mode: Optional[FallbackMode] = None
    user_technical_work: bool = False  # True if user must do technical work (FAIL)
    user_technical_work_acknowledged: bool = False  # Explicit acknowledgment to bypass
    driver: Optional[str] = None  # Which driver will be used
    status: str = "draft"  # draft, approved, executing, verified, complete

    @model_validator(mode="before")
    @classmethod
    def reject_ad_hoc_contract_exemptions(cls, data: Any):
        """Reject legacy flags that bypass reviewed contract-type semantics."""
        if isinstance(data, dict) and "capability_build" in data:
            raise ValueError(
                "capability_build is an unreviewed gate exemption. Use "
                "contract_type: build_capability with an explicit "
                "target_completion_status."
            )
        return data

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
    def validate_raw_request_present(self):
        """Contracts must preserve the user's original words for review."""
        if not self.raw_request or not self.raw_request.strip():
            raise ValueError(
                "Contract must include raw_request with the user's exact words. "
                "Review must compare delivery against the original request, not only "
                "against the rewritten contract."
            )
        return self

    @model_validator(mode="after")
    def validate_source_system_declaration(self):
        """The structured declaration may not contradict the raw request."""
        if (
            _request_implies_source_system_access(self.raw_request)
            and not self.source_system_request.requested
        ):
            raise ValueError(
                "raw_request implies source-system access, so "
                "source_system_request.requested must be true. Agents may not "
                "disable source-access gates by setting this field to false."
            )
        if self.source_system_request.requested and not self.source_system_request.system:
            raise ValueError(
                "source_system_request.system is required when requested is true."
            )
        return self

    @model_validator(mode="after")
    def validate_contract_lifecycle(self):
        """Contract type determines the only completion states it may target."""
        allowed_statuses = {
            ContractType.BUILD_CAPABILITY: {
                CompletionStatus.CAPABILITY_BUILT,
                CompletionStatus.CAPABILITY_READY_NOT_CONNECTED,
            },
            ContractType.CONNECT_CAPABILITY: {
                CompletionStatus.CAPABILITY_CONNECTED,
            },
            ContractType.EXECUTE_WORKFLOW: {
                CompletionStatus.OUTCOME_DELIVERED,
            },
            ContractType.FRAMEWORK_CHANGE: {
                CompletionStatus.CAPABILITY_BUILT,
            },
        }
        if self.target_completion_status not in allowed_statuses[self.contract_type]:
            allowed = ", ".join(
                sorted(status.value for status in allowed_statuses[self.contract_type])
            )
            raise ValueError(
                f"contract_type {self.contract_type.value} may only target: {allowed}."
            )

        if (
            self.contract_type == ContractType.FRAMEWORK_CHANGE
            and not _request_implies_framework_change(self.raw_request)
        ):
            raise ValueError(
                "framework_change is reserved for raw requests that explicitly "
                "ask to change PocketOps framework, architecture, gates, schema, "
                "or protocol."
            )

        if (
            self.contract_type == ContractType.BUILD_CAPABILITY
            and self.source_system_request.requested
        ):
            if not self.access_discovery:
                raise ValueError(
                    "A source-system build_capability contract requires "
                    "access_discovery."
                )
            if not self.access_discovery.has_viable_access_path():
                raise ValueError(
                    "A source-system build_capability contract requires a viable "
                    "API, SDK/CLI, delegated-provider, browser, or credential flow."
                )

        if (
            self.contract_type == ContractType.CONNECT_CAPABILITY
            and not self.source_system_request.requested
        ):
            raise ValueError(
                "connect_capability requires source_system_request.requested: true "
                "and the external system being connected."
            )

        if (
            self.contract_type
            in (ContractType.CONNECT_CAPABILITY, ContractType.EXECUTE_WORKFLOW)
            and not self.source_system_request.requested
            and _request_implies_source_system_access(self.raw_request)
        ):
            raise ValueError(
                f"{self.contract_type.value} must preserve requested source-system access."
            )
        return self

    @model_validator(mode="after")
    def validate_no_user_technical_work(self):
        """
        Reject contracts that require user to do technical work.

        If the contract explicitly declares user_technical_work: true,
        validation fails unless user_technical_work_acknowledged: true
        is also set (indicating the user accepted this limitation).

        Technical work includes:
        - Manually exporting files from websites
        - Writing SQL queries or code
        - Editing configuration files
        - Setting up cron jobs or automation
        """
        if self.user_technical_work and not self.user_technical_work_acknowledged:
            raise ValueError(
                "Contract requires user to do technical work. "
                "This violates the automation principle - the agent should handle all technical tasks. "
                "Either redesign to eliminate user technical work, or set "
                "user_technical_work_acknowledged: true if this is intentional."
            )
        return self

    @model_validator(mode="after")
    def validate_no_unacknowledged_outcome_downgrade(self):
        """
        Reject contracts that turn source-system retrieval into a fallback.

        If a user asks for data from a system/account, the agent must pursue
        access paths first. Manual files, copy/paste, mock data, and sandbox-only
        modes are allowed only when the user explicitly asked for that mode or
        explicitly accepts it after access discovery.
        """
        requested_source_access = (
            self.source_system_request.requested
            or _request_implies_source_system_access(self.raw_request)
        )
        request_allows_fallback = _request_explicitly_allows_fallback(self.raw_request)

        contract_text = " ".join(
            [
                self.outcome,
                " ".join(check.description for check in self.verification.checks),
                " ".join(check.expected or "" for check in self.verification.checks),
                " ".join(constraint.description for constraint in self.constraints),
            ]
        )
        active_fallback = bool(self.fallback_mode and self.fallback_mode.active)
        detected_fallback = active_fallback or _contract_uses_fallback(contract_text)

        if requested_source_access and detected_fallback and not request_allows_fallback:
            accepted_fallback = bool(
                self.fallback_mode
                and self.fallback_mode.accepted_after_access_discovery
            )

            if not accepted_fallback:
                raise ValueError(
                    "Contract appears to downgrade a source-system request into a "
                    "fallback mode such as manual file input, copy/paste, mock data, "
                    "or sandbox-only data. This violates outcome preservation. Pursue "
                    "API, SDK/CLI, delegated provider, browser-assisted, or credential "
                    "flow access first. If fallback is truly intended, set "
                    "fallback_mode.type and fallback_mode.accepted_after_access_discovery "
                    "only after explicit user acceptance."
                )

            if not self.access_discovery or not self.access_discovery.has_attempted_access_path():
                raise ValueError(
                    "Fallback for a source-system request requires "
                    "access_discovery documenting attempted API, SDK/CLI, delegated "
                    "provider, browser, or credential-flow paths."
                )

        return self

    @classmethod
    def create(
        cls,
        raw_request: str,
        contract_type: ContractType | str,
        target_completion_status: CompletionStatus | str,
        outcome: str,
        checks: list[dict],
        constraints: list[dict] | None = None,
        source_system_request: dict | None = None,
        access_discovery: dict | None = None,
        fallback_mode: dict | None = None,
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
            raw_request=raw_request,
            contract_type=contract_type,
            target_completion_status=target_completion_status,
            outcome=outcome,
            verification=Verification(checks=verification_checks),
            constraints=constraint_list,
            source_system_request=SourceSystemRequest(**source_system_request) if source_system_request else SourceSystemRequest(),
            access_discovery=AccessDiscovery(**access_discovery) if access_discovery else None,
            fallback_mode=FallbackMode(**fallback_mode) if fallback_mode else None,
            driver=driver,
        )
