"""
Base types and enums used across manifest schemas.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel


class TrustStatus(str, Enum):
    """Trust level of a component."""
    DRAFT = "draft"
    TESTED = "tested"
    INTEGRATION_VERIFIED = "integration-verified"
    PRODUCTION_VERIFIED = "production-verified"


class RiskLevel(str, Enum):
    """Risk level for operations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Scope(str, Enum):
    """Scope of impact for an operation."""
    READ_ONLY = "read-only"
    SINGLE_RECORD = "single-record"
    BATCH = "batch"
    DESTRUCTIVE = "destructive"


class ComponentKind(str, Enum):
    """Types of PocketOps components."""
    TRANSPORT = "transport"
    ADAPTER = "adapter"
    DRIVER = "driver"


class Trust(BaseModel):
    """Trust metadata for a component."""
    status: TrustStatus = TrustStatus.DRAFT
    last_verified: Optional[str] = None
    notes: Optional[str] = None


class Dependencies(BaseModel):
    """Component dependencies."""
    runtime: list[str] = []
    packages: list[str] = []
    system: list[str] = []


class ConfigOption(BaseModel):
    """Configuration option definition."""
    name: str
    type: str
    required: bool = False
    default: Optional[str | int | float | bool | list] = None
    description: Optional[str] = None


class BaseManifest(BaseModel):
    """Base class for all manifest types."""
    name: str
    kind: ComponentKind
    version: str
    description: Optional[str] = None
    trust: Trust = Trust()
