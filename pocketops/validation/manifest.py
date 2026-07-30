"""
Manifest validation utilities.

Validates manifests against Pydantic schemas and checks dependencies.
"""

from pathlib import Path
from typing import Union
from dataclasses import dataclass, field

import yaml
from pydantic import ValidationError

from pocketops.schemas import (
    TransportManifest,
    AdapterManifest,
    DriverManifest,
)


@dataclass
class ManifestError:
    """Error encountered during manifest validation."""
    path: str
    kind: str
    message: str
    details: list[str] = field(default_factory=list)


def _detect_kind(data: dict) -> str:
    """Detect the kind of manifest from its data."""
    return data.get("kind", "unknown")


def _get_schema_for_kind(kind: str):
    """Get the Pydantic schema for a manifest kind."""
    schemas = {
        "transport": TransportManifest,
        "adapter": AdapterManifest,
        "driver": DriverManifest,
    }
    return schemas.get(kind)


def validate_manifest(
    path: Union[str, Path],
) -> tuple[bool, Union[TransportManifest, AdapterManifest, DriverManifest, None], list[ManifestError]]:
    """
    Validate a single manifest file.

    Returns:
        (success, parsed_manifest, errors)
    """
    path = Path(path)
    errors = []

    if not path.exists():
        errors.append(ManifestError(
            path=str(path),
            kind="unknown",
            message="File not found",
        ))
        return False, None, errors

    # Load YAML
    try:
        with open(path) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        errors.append(ManifestError(
            path=str(path),
            kind="unknown",
            message=f"Invalid YAML: {e}",
        ))
        return False, None, errors

    if not data:
        errors.append(ManifestError(
            path=str(path),
            kind="unknown",
            message="Empty manifest file",
        ))
        return False, None, errors

    # Detect kind
    kind = _detect_kind(data)
    if kind == "unknown":
        errors.append(ManifestError(
            path=str(path),
            kind="unknown",
            message="Manifest missing 'kind' field",
        ))
        return False, None, errors

    # Get schema
    schema = _get_schema_for_kind(kind)
    if not schema:
        errors.append(ManifestError(
            path=str(path),
            kind=kind,
            message=f"Unknown manifest kind: {kind}",
        ))
        return False, None, errors

    # Validate against schema
    try:
        manifest = schema(**data)
        return True, manifest, []
    except ValidationError as e:
        details = []
        for error in e.errors():
            loc = ".".join(str(l) for l in error["loc"])
            details.append(f"{loc}: {error['msg']}")

        errors.append(ManifestError(
            path=str(path),
            kind=kind,
            message="Schema validation failed",
            details=details,
        ))
        return False, None, errors


def validate_all_manifests(
    project_root: Union[str, Path] = ".",
) -> tuple[bool, dict, list[ManifestError]]:
    """
    Validate all manifests in the project.

    Returns:
        (all_valid, manifests_by_kind, all_errors)
    """
    project_root = Path(project_root)
    errors = []
    manifests = {
        "transport": {},
        "adapter": {},
        "driver": {},
    }

    # Find all manifest files
    manifest_dirs = ["transports", "adapters", "drivers"]

    for dir_name in manifest_dirs:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            continue

        for manifest_path in dir_path.glob("**/manifest.yaml"):
            success, manifest, manifest_errors = validate_manifest(manifest_path)
            errors.extend(manifest_errors)

            if success and manifest:
                kind = manifest.kind.value
                manifests[kind][manifest.name] = manifest

    all_valid = len(errors) == 0
    return all_valid, manifests, errors


def validate_dependencies(
    project_root: Union[str, Path] = ".",
) -> tuple[bool, list[ManifestError]]:
    """
    Validate that all declared dependencies exist.

    Checks:
    - Adapters depend on existing transports
    - Drivers depend on existing adapters
    """
    project_root = Path(project_root)
    errors = []

    # First, validate and collect all manifests
    _, manifests, validation_errors = validate_all_manifests(project_root)
    if validation_errors:
        # Can't check dependencies if manifests are invalid
        return False, validation_errors

    transports = set(manifests["transport"].keys())
    adapters = set(manifests["adapter"].keys())

    # Check adapter dependencies
    for name, adapter in manifests["adapter"].items():
        # Use helper method to get transport names
        transport_deps = adapter.depends_on.get_transport_names()
        for transport_dep in transport_deps:
            if transport_dep not in transports:
                errors.append(ManifestError(
                    path=f"adapters/{name}/manifest.yaml",
                    kind="adapter",
                    message=f"Depends on non-existent transport: {transport_dep}",
                    details=[f"Available transports: {', '.join(sorted(transports)) or 'none'}"],
                ))

    # Check driver dependencies
    for name, driver in manifests["driver"].items():
        # Use helper method to get adapter names
        adapter_deps = driver.depends_on.get_adapter_names()
        for adapter_dep in adapter_deps:
            if adapter_dep not in adapters:
                errors.append(ManifestError(
                    path=f"drivers/{name}/manifest.yaml",
                    kind="driver",
                    message=f"Depends on non-existent adapter: {adapter_dep}",
                    details=[f"Available adapters: {', '.join(sorted(adapters)) or 'none'}"],
                ))

    all_valid = len(errors) == 0
    return all_valid, errors


def format_errors(errors: list[ManifestError]) -> str:
    """Format errors for display."""
    if not errors:
        return "No errors"

    lines = []
    for error in errors:
        lines.append(f"\n{error.path} ({error.kind}):")
        lines.append(f"  {error.message}")
        for detail in error.details:
            lines.append(f"    - {detail}")

    return "\n".join(lines)
