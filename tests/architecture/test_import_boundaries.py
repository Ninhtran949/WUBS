"""Inspect every import, including relative and TYPE_CHECKING imports."""

import ast
import sys
from importlib.util import resolve_name
from pathlib import Path

import pytest

pytestmark = pytest.mark.architecture
PACKAGE = "web_stress_lab"
ROOT = Path(__file__).resolve().parents[2] / "src" / PACKAGE
ALLOWED = {
    "domain": {"domain"},
    "application": {"domain", "application"},
    "infrastructure": {"domain", "application", "infrastructure"},
    "interfaces": {"domain", "application", "interfaces"},
    "lab_app": {"lab_app"},
}


def violations(source: str, module: str) -> list[str]:
    layer = module.split(".")[1]
    found = []
    for node in ast.walk(ast.parse(source)):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            imported = "." * node.level + (node.module or "")
            name = resolve_name(imported, module.rpartition(".")[0])
            names = [name] + [f"{name}.{alias.name}" for alias in node.names]
        for name in names:
            root = name.split(".")[0]
            parts = name.split(".")
            if root in {"locust", "gevent"} and not module.startswith(
                f"{PACKAGE}.infrastructure.load.workload"
            ):
                found.append(name)
            if layer in {"domain", "application"} and root not in (
                sys.stdlib_module_names | {PACKAGE}
            ):
                found.append(name)
            if (
                root == PACKAGE
                and len(parts) > 1
                and parts[1] not in ALLOWED[layer]
                and module != f"{PACKAGE}.interfaces.bootstrap"
            ):
                found.append(name)
    return found


@pytest.mark.parametrize(
    ("module", "source"),
    [
        ("domain.values", "import pydantic"),
        ("domain.values", "from ..application import ports"),
        ("application.run", "from ..infrastructure import browser"),
        ("application.run", "if TYPE_CHECKING:\n    import playwright"),
        ("infrastructure.storage", "from ..interfaces import cli"),
        ("interfaces.cli", "from ..infrastructure import storage"),
        ("lab_app.app", "from ..domain import values"),
        ("infrastructure.load.runner", "import locust"),
        ("application.run", "import gevent"),
    ],
)
def test_detects_forbidden_imports(module: str, source: str) -> None:
    assert violations(source, f"{PACKAGE}.{module}")


def test_all_production_modules_follow_boundaries() -> None:
    assert ROOT.is_dir(), "Product package is missing"
    for path in ROOT.rglob("*.py"):
        relative = path.relative_to(ROOT).with_suffix("")
        if len(relative.parts) < 2:
            continue
        module = ".".join((PACKAGE, *relative.parts))
        assert not violations(path.read_text(encoding="utf-8"), module), path
