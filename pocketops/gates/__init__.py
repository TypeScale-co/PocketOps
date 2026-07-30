"""
PocketOps gate system.

Gates enforce constraints at phase transitions, preventing
progression without meeting requirements.
"""

from pocketops.gates.registry import Phase, GateRegistry, GateResult

__all__ = [
    "Phase",
    "GateRegistry",
    "GateResult",
]
