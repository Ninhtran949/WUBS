"""Run the installed entry points outside the source checkout."""

import json
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


def test_report_reads_synthetic_outcomes_outside_checkout(tmp_path: Path) -> None:
    from web_stress_lab.domain.results import CaseOutcome
    from web_stress_lab.infrastructure.storage import FileResultSink
    from web_stress_lab.interfaces.configuration import load_experiment

    fixture = Path(__file__).resolve().parents[2] / "fixtures/experiments/local-browser.yaml"
    sink = FileResultSink(tmp_path / "reports")
    manifest = sink.start(load_experiment(fixture), "synthetic-cli", planned_cases=1)
    sink.record(CaseOutcome("case-1", "LOGIN", "COMPLETED", manifest.started_at,
                            manifest.started_at, 0.25))
    sink.finish("COMPLETED")
    root = tmp_path / "reports" / manifest.run_id
    before = {path.name: path.read_bytes() for path in root.iterdir()}
    result = invoke(tmp_path, "report", manifest.run_id, "--json")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True and payload["read_only"] is True
    assert payload["report"]["data_source"] == "synthetic"
    assert payload["report"]["recorded_cases"] == 1
    assert payload["report"]["reporting_complete"] is True
    assert {path.name: path.read_bytes() for path in root.iterdir()} == before
    human = invoke(tmp_path, "report", manifest.run_id)
    assert human.returncode == 0
    assert "COMPLETED" in human.stdout and "synthetic" in human.stdout


def test_report_missing_or_unsafe_run_is_redacted_exit_four(tmp_path: Path) -> None:
    for run_id in ("missing", "../SECRET_CANARY"):
        result = invoke(tmp_path, "report", run_id, "--json")
        assert result.returncode == 4
        payload = json.loads(result.stdout)
        assert payload["ok"] is False
        assert payload["error"]["category"] == "ReportingError"
        assert "SECRET_CANARY" not in result.stdout + result.stderr
    assert not (tmp_path / "reports").exists()


def test_report_partial_manifest_does_not_claim_execution_success(tmp_path: Path) -> None:
    from web_stress_lab.infrastructure.storage import FileResultSink
    from web_stress_lab.interfaces.configuration import load_experiment

    fixture = Path(__file__).resolve().parents[2] / "fixtures/experiments/local-browser.yaml"
    FileResultSink(tmp_path / "reports").start(load_experiment(fixture), "partial", planned_cases=2)
    result = invoke(tmp_path, "report", "partial", "--json")
    assert result.returncode == 0
    report = json.loads(result.stdout)["report"]
    assert report["status"] == "RUNNING"
    assert report["reporting_complete"] is False
    assert report["unrecorded_cases"] == 2
    assert not (tmp_path / "reports/partial/summary.json").exists()


def test_version_matches_installed_distribution(tmp_path: Path) -> None:
    result = invoke(tmp_path, "--version")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == f"stresslab {version('web-stress-lab')}"


def test_unsupported_command_is_usage_error(tmp_path: Path) -> None:
    result = invoke(tmp_path, "nonexistent")
    assert result.returncode == 2
    assert "error:" in result.stderr


def test_validate_config_returns_static_json_outside_checkout(tmp_path: Path) -> None:
    fixture = (
        Path(__file__).resolve().parents[2] / "fixtures/experiments/local-browser.yaml"
    )
    result = invoke(tmp_path, "validate-config", str(fixture), "--json")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["validation"] == "static"
    assert payload["execution_checked"] is False
    assert payload["experiment"]["origin"] == "http://127.0.0.1:8765"
    assert result.stderr == ""


def test_validate_config_has_useful_human_output(tmp_path: Path) -> None:
    fixture = (
        Path(__file__).resolve().parents[2] / "fixtures/experiments/local-http.json"
    )
    result = invoke(tmp_path, "validate-config", str(fixture))
    assert result.returncode == 0, result.stderr
    assert "static" in result.stdout.lower()
    assert "http" in result.stdout
    assert "HTTP_HEALTH" in result.stdout


def test_invalid_json_reports_exit_two_without_source_excerpt(tmp_path: Path) -> None:
    fixture = tmp_path / "bad.json"
    fixture.write_text('{"SENSITIVE_KEY":"SENSITIVE_VALUE"}', encoding="utf-8")
    result = invoke(tmp_path, "validate-config", str(fixture), "--json")
    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["error"]["category"] == "ConfigurationError"
    assert payload["error"]["issues"]
    assert "SENSITIVE" not in result.stdout + result.stderr


def test_scope_error_has_distinct_exit_code(tmp_path: Path) -> None:
    fixture = (
        Path(__file__).resolve().parents[2] / "fixtures/experiments/local-http.json"
    )
    document = json.loads(fixture.read_text(encoding="utf-8"))
    document["target"]["mode"] = "external_read_only"
    invalid = tmp_path / "external.json"
    invalid.write_text(json.dumps(document), encoding="utf-8")
    result = invoke(tmp_path, "validate-config", str(invalid), "--json")
    assert result.returncode == 3
    assert json.loads(result.stdout)["error"]["category"] == "ScopeViolationError"


def test_unknown_fields_and_values_never_reach_cli_diagnostics(tmp_path: Path) -> None:
    fixture = (
        Path(__file__).resolve().parents[2] / "fixtures/experiments/local-http.json"
    )
    document = json.loads(fixture.read_text(encoding="utf-8"))
    document["SENSITIVE_KEY"] = "SENSITIVE_VALUE"
    invalid = tmp_path / "invalid.json"
    invalid.write_text(json.dumps(document), encoding="utf-8")
    result = invoke(tmp_path, "validate-config", str(invalid), "--json")
    assert result.returncode == 2
    assert "SENSITIVE" not in result.stdout + result.stderr
    assert json.loads(result.stdout)["error"]["issues"]


@pytest.mark.parametrize(
    "scalar",
    [
        "!!bool SENSITIVE_VALUE",
        '!!int ""',
        '!!float ""',
        '!!float "' + ":".join(["1"] * 200) + '"',
    ],
    ids=["invalid-bool", "empty-int", "empty-float", "float-overflow"],
)
def test_malformed_yaml_scalar_constructors_stay_sanitized_json(
    tmp_path: Path, scalar: str
) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text(f"seed: {scalar}\n", encoding="utf-8")
    result = invoke(tmp_path, "validate-config", str(path), "--json")
    assert result.returncode == 2, result.stderr
    assert json.loads(result.stdout)["error"]["category"] == "ConfigurationError"
    assert result.stderr == ""
    assert "SENSITIVE" not in result.stdout


def test_human_error_output_is_sanitized_and_uses_stderr(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text("seed: !!bool SENSITIVE_VALUE\n", encoding="utf-8")
    result = invoke(tmp_path, "validate-config", str(path))
    assert result.returncode == 2
    assert result.stdout == ""
    assert "ConfigurationError" in result.stderr
    assert "SENSITIVE" not in result.stderr
