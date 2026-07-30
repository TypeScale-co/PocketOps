"""
PocketOps - Runtime enforcement for agent workflows.

This package provides:
- Pydantic schemas for manifest validation
- Gate system for phase transitions
- Layer boundary enforcement (static + runtime)

Environment variables:
- POCKETOPS_STRICT=1: Enable runtime import guard on package load
"""

import os

from pocketops.schemas import (
    TransportManifest,
    AdapterManifest,
    CompletionStatus,
    ContractType,
    DriverManifest,
    OutcomeContract,
)
from pocketops.gates import Phase, GateRegistry, GateResult
from pocketops.validation import (
    load_manifest,
    load_contract,
    ManifestLoadError,
    LayerViolationError,
    install_import_guard,
)
from pocketops.workflow import (
    create_run,
    complete_run,
    RunRecord,
    RunCreationError,
    CompletionError,
    CompletionResult,
)

__version__ = "1.0.0"

__all__ = [
    # Schemas
    "TransportManifest",
    "AdapterManifest",
    "DriverManifest",
    "ContractType",
    "CompletionStatus",
    "OutcomeContract",
    # Gates
    "Phase",
    "GateRegistry",
    "GateResult",
    # Validation (enforced loading)
    "load_manifest",
    "load_contract",
    "ManifestLoadError",
    # Layer enforcement
    "LayerViolationError",
    "install_import_guard",
    # Workflow lifecycle (REQUIRED functions)
    "create_run",       # Call BEFORE execution
    "complete_run",     # Call AFTER verification
    "RunRecord",
    "RunCreationError",
    "CompletionError",
    "CompletionResult",
]

# Auto-install import guard in strict mode
if os.environ.get("POCKETOPS_STRICT", "").lower() in ("1", "true", "yes"):
    install_import_guard()
