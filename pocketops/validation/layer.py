"""
Layer boundary enforcement.

Uses AST analysis to detect import violations:
- Drivers can only import from adapters.*
- Adapters can only import from transports.*
- Transports cannot import from adapters or drivers

Also provides runtime import blocking via install_import_guard().
"""

import ast
import sys
import inspect
from pathlib import Path
from dataclasses import dataclass
from typing import Any, ClassVar, Union, cast


class LayerViolationError(ImportError):
    """Raised when an import violates layer boundaries at runtime."""

    def __init__(self, importer_layer: str, imported_module: str, importer_file: str):
        self.importer_layer = importer_layer
        self.imported_module = imported_module
        self.importer_file = importer_file
        super().__init__(
            f"Layer violation: {importer_layer} cannot import from {imported_module}\n"
            f"  Importing file: {importer_file}\n"
            f"  Rule: {self._get_rule()}"
        )

    def _get_rule(self) -> str:
        rules = {
            "transports": "Transports can only import from transports.* (not adapters or drivers)",
            "adapters": "Adapters can only import from transports.* or adapters.* (not drivers)",
            "drivers": "Drivers can import from any layer",
        }
        return rules.get(self.importer_layer, "Unknown layer")


@dataclass
class LayerViolation:
    """A layer boundary violation."""
    file: str
    line: int
    layer: str  # transport, adapter, or driver
    imported: str  # What was imported
    message: str


# Define layer hierarchy (lower index = lower layer)
LAYERS = {
    "transports": 0,
    "adapters": 1,
    "drivers": 2,
}

# What each layer can import
ALLOWED_IMPORTS = {
    "transports": {
        # Transports can't import from adapters or drivers
        "forbidden": ["adapters", "drivers"],
        "allowed_prefixes": ["transports."],
    },
    "adapters": {
        # Adapters can import from transports, not from drivers
        "forbidden": ["drivers"],
        "allowed_prefixes": ["transports.", "adapters."],
    },
    "drivers": {
        # Drivers can import from adapters (and transitively transports)
        "forbidden": [],
        "allowed_prefixes": ["adapters.", "drivers.", "transports."],
    },
}


class ImportVisitor(ast.NodeVisitor):
    """AST visitor that collects import statements."""

    def __init__(self):
        self.imports: list[tuple[int, str]] = []  # (line_number, module_name)

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.imports.append((node.lineno, alias.name))
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            self.imports.append((node.lineno, node.module))
        self.generic_visit(node)


def _detect_layer(file_path: Path) -> str | None:
    """Detect which layer a file belongs to."""
    parts = file_path.parts

    for layer_name in LAYERS:
        if layer_name in parts:
            return layer_name

    return None


def _is_pocketops_import(module: str) -> bool:
    """Check if an import is a PocketOps layer import."""
    return any(
        module.startswith(prefix)
        for prefix in ["transports", "adapters", "drivers"]
    )


def check_file_imports(
    file_path: Union[str, Path],
) -> list[LayerViolation]:
    """
    Check a single Python file for layer violations.

    Returns list of violations found.
    """
    file_path = Path(file_path)
    violations = []

    layer = _detect_layer(file_path)
    if not layer:
        # File is not in a recognized layer
        return []

    # Parse the file
    try:
        with open(file_path) as f:
            source = f.read()
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError:
        # Can't parse - skip this file
        return []

    # Collect imports
    visitor = ImportVisitor()
    visitor.visit(tree)

    # Check each import
    rules = ALLOWED_IMPORTS[layer]
    forbidden = rules["forbidden"]

    for lineno, module in visitor.imports:
        if not _is_pocketops_import(module):
            # Not a PocketOps import, skip
            continue

        # Check if import violates layer boundaries
        for forbidden_prefix in forbidden:
            if module.startswith(forbidden_prefix):
                violations.append(LayerViolation(
                    file=str(file_path),
                    line=lineno,
                    layer=layer,
                    imported=module,
                    message=f"{layer} cannot import from {forbidden_prefix}",
                ))

    return violations


def check_layer_violations(
    project_root: Union[str, Path] = ".",
) -> list[LayerViolation]:
    """
    Check all Python files in the project for layer violations.

    Returns list of all violations found.
    """
    project_root = Path(project_root)
    violations = []

    # Check each layer directory
    for layer_name in LAYERS:
        layer_dir = project_root / layer_name
        if not layer_dir.exists():
            continue

        # Find all Python files
        for py_file in layer_dir.glob("**/*.py"):
            file_violations = check_file_imports(py_file)
            violations.extend(file_violations)

    return violations


def format_violations(violations: list[LayerViolation]) -> str:
    """Format violations for display."""
    if not violations:
        return "No layer violations found"

    lines = ["Layer violations found:"]
    for v in violations:
        lines.append(f"  {v.file}:{v.line}")
        lines.append(f"    {v.message}")
        lines.append(f"    imported: {v.imported}")

    return "\n".join(lines)


# =============================================================================
# Runtime Import Guard
# =============================================================================

class LayerImportGuard:
    """
    Meta path finder that blocks imports violating layer boundaries.

    Install with install_import_guard() to enforce layer rules at runtime.
    This catches dynamic imports that AST analysis would miss.
    """

    _instance: ClassVar["LayerImportGuard | None"] = None
    _installed: ClassVar[bool] = False

    def __init__(self):
        self.enabled = True

    def find_module(self, fullname: str, path=None):
        """Called by Python import system. Returns self if we should block."""
        if not self.enabled:
            return None

        # Only check PocketOps layer imports
        if not _is_pocketops_import(fullname):
            return None

        # Determine who is importing
        importer_file = self._get_importer_file()
        if not importer_file:
            return None

        importer_layer = _detect_layer(Path(importer_file))
        if not importer_layer:
            return None

        # Check if this import is forbidden
        rules = ALLOWED_IMPORTS.get(importer_layer, {})
        forbidden = rules.get("forbidden", [])

        for forbidden_prefix in forbidden:
            if fullname.startswith(forbidden_prefix):
                # Block this import by raising in load_module
                self._pending_violation = LayerViolationError(
                    importer_layer=importer_layer,
                    imported_module=fullname,
                    importer_file=importer_file,
                )
                return self

        return None

    def load_module(self, fullname: str):
        """Called if find_module returned self. Raises the violation."""
        if hasattr(self, '_pending_violation'):
            violation = self._pending_violation
            del self._pending_violation
            raise violation
        return None

    def _get_importer_file(self) -> str | None:
        """Get the file that initiated the import."""
        # Walk up the stack to find who called import
        for frame_info in inspect.stack():
            filename = frame_info.filename

            # Skip internal Python files and pocketops validation
            if 'importlib' in filename:
                continue
            if 'pocketops/validation' in filename:
                continue
            if filename.startswith('<'):
                continue

            # Check if this file is in a layer directory
            if any(layer in filename for layer in ['transports', 'adapters', 'drivers']):
                return filename

        return None


def install_import_guard() -> LayerImportGuard:
    """
    Install the runtime import guard.

    Call this early in your application to enforce layer boundaries
    at runtime, catching dynamic imports that AST analysis misses.

    Returns:
        The guard instance (can be used to temporarily disable with guard.enabled = False)
    """
    if LayerImportGuard._installed:
        instance = LayerImportGuard._instance
        if instance is not None:
            return instance

    guard = LayerImportGuard()
    sys.meta_path.insert(0, cast(Any, guard))
    LayerImportGuard._instance = guard
    LayerImportGuard._installed = True

    return guard


def uninstall_import_guard() -> None:
    """Remove the import guard (useful for testing)."""
    if not LayerImportGuard._installed:
        return

    if LayerImportGuard._instance in sys.meta_path:
        sys.meta_path.remove(LayerImportGuard._instance)

    LayerImportGuard._instance = None
    LayerImportGuard._installed = False
