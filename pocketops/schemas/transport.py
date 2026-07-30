"""
Transport manifest schema.

Transports are the lowest layer - they handle raw communication
(HTTP, CLI, SQL, filesystem, etc.) without business logic.
"""

from typing import Optional
from pydantic import BaseModel

from pocketops.schemas.base import (
    BaseManifest,
    ComponentKind,
    Dependencies,
    ConfigOption,
    Trust,
)


class DryRunSupport(BaseModel):
    """Dry-run capability metadata."""
    dry_run: bool = False
    dry_run_method: Optional[str] = None


class TransportManifest(BaseManifest):
    """
    Manifest for transport components.

    Transports handle raw communication with external systems.
    They are the foundation layer and cannot depend on adapters or drivers.
    """
    kind: ComponentKind = ComponentKind.TRANSPORT
    capabilities: list[str] = []
    supports: DryRunSupport = DryRunSupport()
    dependencies: Dependencies = Dependencies()
    configuration: list[ConfigOption] = []
    trust: Trust = Trust()

    class Config:
        extra = "allow"  # Allow additional fields like 'authentication'
