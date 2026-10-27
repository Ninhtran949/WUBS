"""Run the installed entry points outside the source checkout."""

import os
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration


def invoke(tmp_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    return subprocess.run(
        [sys.executable, "-I", "-m", "web_stress_lab", *args],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )


def test_help_describes_available_capability(tmp_path: Path) -> None:
    result = invoke(tmp_path, "--help")
    assert result.returncode == 0, result.stderr
    assert "stresslab" in result.stdout
    assert "--version" in result.stdout


def test_version_matches_installed_distribution(tmp_path: Path) -> None:
    result = invoke(tmp_path, "--version")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == f"stresslab {version('web-stress-lab')}"


def test_unsupported_command_is_usage_error(tmp_path: Path) -> None:
    result = invoke(tmp_path, "nonexistent")
    assert result.returncode == 2
    assert "error:" in result.stderr
