"""
Layer boundary enforcement.

Uses AST analysis to detect import violations:
- Drivers can only import from adapters.*
- Adapters can only import from transports.*
- Transports cannot import from adapters or drivers
"""

import ast
from pathlib import Path
from dataclasses import dataclass
from typing import Union


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
