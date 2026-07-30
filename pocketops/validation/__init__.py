"""
PocketOps validation utilities.

Provides manifest validation, dependency checking, and layer enforcement.

IMPORTANT: Use load_manifest() and load_contract() to load files.
These enforce validation at load time, not just during verification.
"""

from pocketops.validation.manifest import (
    load_manifest,
    load_contract,
    validate_manifest,
    validate_all_manifests,
    validate_dependencies,
    ManifestError,
    ManifestLoadError,
)
from pocketops.validation.layer import (
    check_layer_violations,
    LayerViolation,
    LayerViolationError,
    install_import_guard,
    uninstall_import_guard,
)

__all__ = [
    # Primary API - enforces validation at load time
    "load_manifest",
    "load_contract",
    "ManifestLoadError",
    # Validation API - for batch checking
    "validate_manifest",
    "validate_all_manifests",
    "validate_dependencies",
    "ManifestError",
    # Layer enforcement - static analysis
    "check_layer_violations",
    "LayerViolation",
    # Layer enforcement - runtime blocking
    "LayerViolationError",
    "install_import_guard",
    "uninstall_import_guard",
]
