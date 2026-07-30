"""
PocketOps workflow enforcement.

This module provides the ONLY valid way to start and complete a workflow.

- create_run() MUST be called before execution starts
- complete_run() MUST be called to finish (enforces all gates)
"""

from pocketops.workflow.completion import (
    create_run,
    complete_run,
    RunRecord,
    RunCreationError,
    CompletionError,
    CompletionResult,
)

__all__ = [
    # Starting a run
    "create_run",
    "RunRecord",
    "RunCreationError",
    # Completing a run
    "complete_run",
    "CompletionError",
    "CompletionResult",
]
