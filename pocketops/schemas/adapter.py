"""
Adapter manifest schema.

Adapters wrap transports to provide domain-specific interfaces
(e.g., Slack, HubSpot, GitHub). They can only depend on transports.
"""

from typing import Optional, Union
from pydantic import BaseModel, model_validator, field_validator

from pocketops.schemas.base import (
    BaseManifest,
    ComponentKind,
    ConfigOption,
    Trust,
    RiskLevel,
    Scope,
)


class Operation(BaseModel):
    """An operation exposed by an adapter."""
    name: str
    description: Optional[str] = None
    risk: RiskLevel = RiskLevel.LOW
    scope: Scope = Scope.READ_ONLY
    requires_approval: bool = False
    dry_run_capable: bool = False


class TransportDependency(BaseModel):
    """A transport dependency with optional version constraint."""
    name: str
    version: Optional[str] = None

    class Config:
        extra = "allow"


class AdapterDependencies(BaseModel):
    """Adapter-specific dependencies (must include transports)."""
    transports: list[Union[str, TransportDependency]] = []
    runtime: list[str] = []
    packages: list[str] = []

    @field_validator("transports", mode="before")
    @classmethod
    def normalize_transports(cls, v):
        """Normalize transport dependencies to consistent format."""
        if not v:
            return []
        result = []
        for item in v:
            if isinstance(item, str):
                result.append(item)
            elif isinstance(item, dict):
                result.append(TransportDependency(**item))
            else:
                result.append(item)
        return result

    def get_transport_names(self) -> list[str]:
        """Get list of transport names (without version info)."""
        names = []
        for t in self.transports:
            if isinstance(t, str):
                names.append(t)
            elif isinstance(t, TransportDependency):
                names.append(t.name)
        return names


class CredentialRequirement(BaseModel):
    """Credential required by the adapter."""
    name: str
    type: str  # e.g., "env", "file", "keychain", "environment_variable"
    description: Optional[str] = None
    required: bool = True

    class Config:
        extra = "allow"  # Allow additional fields like format, scopes


class AdapterManifest(BaseManifest):
    """
    Manifest for adapter components.

    Adapters provide domain-specific interfaces by wrapping transports.
    They MUST depend on at least one transport.
    """
    kind: ComponentKind = ComponentKind.ADAPTER
    depends_on: AdapterDependencies = AdapterDependencies()
    credentials: list[CredentialRequirement] = []
    configuration: list[ConfigOption] = []
    trust: Trust = Trust()

    @model_validator(mode="after")
    def validate_has_transport_dependencies(self):
        """Adapters must depend on at least one transport."""
        transport_names = self.depends_on.get_transport_names()
        if not transport_names:
            raise ValueError(
                f"Adapter '{self.name}' must depend on at least one transport. "
                "Adapters wrap transports; they don't implement raw communication."
            )
        return self

    class Config:
        extra = "allow"  # Allow additional fields like 'provides'
