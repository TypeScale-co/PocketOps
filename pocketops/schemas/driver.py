"""
Driver manifest schema.

Drivers are user-facing workflow scripts that compose adapters.
They are the highest layer and MUST depend on adapters.
"""

from typing import Optional, Union
from pydantic import BaseModel, model_validator, field_validator

from pocketops.schemas.base import (
    BaseManifest,
    ComponentKind,
    Trust,
    RiskLevel,
)


class AdapterDependency(BaseModel):
    """An adapter dependency with optional version and operations."""
    name: str
    version: Optional[str] = None
    operations: list[str] = []

    class Config:
        extra = "allow"


class DriverDependencies(BaseModel):
    """Driver dependencies (must include adapters)."""
    adapters: list[Union[str, AdapterDependency]] = []
    runtime: list[str] = []
    packages: list[str] = []

    @field_validator("adapters", mode="before")
    @classmethod
    def normalize_adapters(cls, v):
        """Normalize adapter dependencies to consistent format."""
        if not v:
            return []
        result = []
        for item in v:
            if isinstance(item, str):
                result.append(item)
            elif isinstance(item, dict):
                result.append(AdapterDependency(**item))
            else:
                result.append(item)
        return result

    def get_adapter_names(self) -> list[str]:
        """Get list of adapter names (without version info)."""
        names = []
        for a in self.adapters:
            if isinstance(a, str):
                names.append(a)
            elif isinstance(a, AdapterDependency):
                names.append(a.name)
        return names


class InputParameter(BaseModel):
    """Input parameter for a driver."""
    name: str
    type: str
    required: bool = True
    description: Optional[str] = None
    default: Optional[str | int | float | bool | list] = None


class OutputSpec(BaseModel):
    """Output specification for a driver."""
    name: str
    type: str
    description: Optional[str] = None


class DriverManifest(BaseManifest):
    """
    Manifest for driver components.

    Drivers are user-facing workflow scripts that compose adapters.
    They MUST depend on at least one adapter - drivers don't implement
    business logic directly, they orchestrate adapters.
    """
    kind: ComponentKind = ComponentKind.DRIVER
    risk: RiskLevel = RiskLevel.LOW
    depends_on: DriverDependencies = DriverDependencies()
    inputs: list[InputParameter] = []
    outputs: list[OutputSpec] = []
    trust: Trust = Trust()

    @model_validator(mode="after")
    def validate_has_adapter_dependencies(self):
        """
        Drivers must depend on at least one adapter.

        This is a core architectural constraint: drivers compose adapters,
        they don't implement business logic or communication directly.
        """
        adapter_names = self.depends_on.get_adapter_names()
        if not adapter_names:
            raise ValueError(
                f"Driver '{self.name}' must depend on at least one adapter. "
                "Drivers compose adapters; they don't implement logic directly."
            )
        return self

    class Config:
        extra = "allow"  # Allow additional fields like 'commands', 'effects', 'verification'
