"""
PocketOps workflow enforcement.

This module provides the ONLY valid way to complete a workflow.
Agents MUST call complete_run() to finalize - it enforces all gates.
"""

from pocketops.workflow.completion import (
    complete_run,
    CompletionError,
    CompletionResult,
)

__all__ = [
    "complete_run",
    "CompletionError",
    "CompletionResult",
]
