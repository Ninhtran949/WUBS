"""Inspect every import, including relative and TYPE_CHECKING imports."""

import ast
import re
import sys
from importlib.util import resolve_name
from pathlib import Path

import pytest

pytestmark = pytest.mark.architecture
PACKAGE = "web_stress_lab"
WORKLOAD_NAMESPACE = f"{PACKAGE}.infrastructure.load.workload"
ROOT = Path(__file__).resolve().parents[2] / "src" / PACKAGE
ALLOWED = {
    "__main__": {"interfaces"},
    "domain": {"domain"},
    "application": {"domain", "application"},
    "infrastructure": {"domain", "application", "infrastructure"},
    "interfaces": {"domain", "application", "interfaces"},
    "lab_app": {"lab_app"},
}


def violations(source: str, module: str) -> list[str]:
    module_parts = module.split(".")
    layer = module_parts[1]
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
            if root in {"locust", "gevent"} and not (
                module == WORKLOAD_NAMESPACE
                or module.startswith(f"{WORKLOAD_NAMESPACE}.")
            ):
                found.append(name)
            if (
                len(module_parts) == 2 or layer in {"domain", "application"}
            ) and root not in (sys.stdlib_module_names | {PACKAGE}):
                found.append(name)
            if (
                root == PACKAGE
                and len(parts) > 1
                and parts[1] not in ALLOWED.get(layer, set())
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
        module = ".".join((PACKAGE, *relative.parts))
        assert not violations(path.read_text(encoding="utf-8"), module), path


@pytest.mark.parametrize("filename", ["__init__.py", "__main__.py", "helper.py"])
@pytest.mark.parametrize("dependency", ["locust", "gevent", "playwright"])
def test_scanner_rejects_forbidden_imports_in_root_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    filename: str,
    dependency: str,
) -> None:
    path = tmp_path / filename
    path.write_text(f"import {dependency}\n", encoding="utf-8")
    monkeypatch.setitem(globals(), "ROOT", tmp_path)
    with pytest.raises(AssertionError, match=re.escape(path.as_posix())):
        test_all_production_modules_follow_boundaries()


@pytest.mark.parametrize(
    ("filename", "source"),
    [
        ("__init__.py", "import sys\n"),
        ("__main__.py", "from .interfaces.cli import main\n"),
        ("helper.py", "from pathlib import Path\n"),
    ],
)
def test_scanner_accepts_valid_root_imports(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    filename: str,
    source: str,
) -> None:
    (tmp_path / filename).write_text(source, encoding="utf-8")
    monkeypatch.setitem(globals(), "ROOT", tmp_path)
    test_all_production_modules_follow_boundaries()


@pytest.mark.parametrize("dependency", ["locust", "gevent"])
@pytest.mark.parametrize("module", ["workload_controller", "workload_helper"])
def test_workload_name_prefix_does_not_grant_load_imports(
    dependency: str, module: str
) -> None:
    assert violations(f"import {dependency}", f"{PACKAGE}.infrastructure.load.{module}")


@pytest.mark.parametrize("dependency", ["locust", "gevent"])
@pytest.mark.parametrize("module", ["workload", "workload.__init__", "workload.case"])
def test_load_imports_remain_allowed_in_workload_namespace(
    dependency: str, module: str
) -> None:
    assert not violations(
        f"import {dependency}", f"{PACKAGE}.infrastructure.load.{module}"
    )
