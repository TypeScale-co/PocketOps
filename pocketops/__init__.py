"""
PocketOps - Runtime enforcement for agent workflows.

This package provides:
- Pydantic schemas for manifest validation
- Gate system for phase transitions
- Layer boundary enforcement
"""

from pocketops.schemas import (
    TransportManifest,
    AdapterManifest,
    DriverManifest,
    OutcomeContract,
)
from pocketops.gates import Phase, GateRegistry, GateResult

__version__ = "1.0.0"

__all__ = [
    "TransportManifest",
    "AdapterManifest",
    "DriverManifest",
    "OutcomeContract",
    "Phase",
    "GateRegistry",
    "GateResult",
]
