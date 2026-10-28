"""Bounded local file parsing, schema safety and side-effect-free validation."""

import dataclasses
import json
import os
import socket
import subprocess
from pathlib import Path

import pytest

from web_stress_lab.domain.errors import ConfigurationError, ScopeViolationError
from web_stress_lab.domain.experiment import BrowserWorkload, HttpWorkload
from web_stress_lab.interfaces.configuration import load_experiment

pytestmark = pytest.mark.integration
FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "experiments"


@pytest.fixture
def document() -> dict[str, object]:
    return {
        "schema_version": 1,
        "engine": "browser",
        "target": {"origin": "http://127.0.0.1:8765"},
        "scope": {
            "allowed_origins": ["http://127.0.0.1:8765"],
            "allowed_scenarios": ["LOGIN"],
        },
        "scenarios": [{"id": "LOGIN"}],
        "accounts": {"catalog": "accounts.synthetic.json"},
    }


def write_config(tmp_path: Path, data: object) -> Path:
    path = tmp_path / "experiment.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_yaml_becomes_an_immutable_domain_experiment() -> None:
    experiment = load_experiment(FIXTURES / "local-browser.yaml")
    assert dataclasses.is_dataclass(experiment)
    assert experiment.schema_version == 1
    assert experiment.engine == "browser"
    assert isinstance(experiment.workload, BrowserWorkload)
    assert experiment.workload.concurrency == 2
    assert experiment.workload.max_cases == 10
    assert experiment.scenarios == ("LOGIN",)
    assert experiment.accounts is not None
    assert experiment.accounts.catalog == FIXTURES / "accounts.synthetic.json"
    assert experiment.output_dir == FIXTURES / "reports"
    assert experiment.limits.max_duration_s == 60
    with pytest.raises(dataclasses.FrozenInstanceError):
        experiment.seed = 10


def test_http_json_has_independent_limits_without_accounts() -> None:
    experiment = load_experiment(FIXTURES / "local-http.json")
    assert isinstance(experiment.workload, HttpWorkload)
    assert experiment.workload.users == 2
    assert experiment.workload.max_requests == 100
    assert experiment.workload.max_rps == 5
    assert experiment.limits.max_duration_s == 30
    assert experiment.accounts is None


def test_paths_are_config_relative_and_not_cwd_relative(
    tmp_path: Path, document: dict[str, object], monkeypatch: pytest.MonkeyPatch
) -> None:
    path = write_config(tmp_path, document)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    experiment = load_experiment(path)
    assert experiment.output_dir == tmp_path / "reports"
    assert not experiment.output_dir.exists()
    assert experiment.accounts is not None
    assert experiment.accounts.catalog == tmp_path / "accounts.synthetic.json"
    assert not experiment.accounts.catalog.exists()


@pytest.mark.parametrize(
    "patch",
    [
        {"schema_version": True},
        {"schema_version": 2},
        {"schema_version": "1"},
        {"seed": -1},
        {"seed": 2**63},
        {"engine": "unknown"},
        {"unexpected": "SENSITIVE_VALUE"},
        {"accounts": None},
        {"workload": {"concurrency": True}},
        {"workload": {"concurrency": 11}},
        {"workload": {"queue_size": 0}},
        {"workload": {"max_cases": 11}},
        {"workload": {"max_attempts": 3}},
        {"workload": {"navigation_timeout_s": float("nan")}},
        {"workload": {"action_timeout_s": float("inf")}},
        {"workload": {"concurrency": "2"}},
        {"workload": {"mode": "soak"}},
        {"workload": {"users": 2}},
        {"limits": {"max_duration_s": 61}},
        {"limits": {"shutdown_timeout_s": 19}},
        {"limits": {"max_duration_s": 10}},
        {"think_time": {"mode": "seeded_random", "min_s": 8, "max_s": 3}},
        {"think_time": {"mode": "fixed", "delay_s": -1}},
        {"artifacts": {"capture": "always"}},
        {"artifacts": {"retention_days": 0}},
        {"scenarios": [{"id": "LOGIN", "mutates_state": False}]},
        {"scenarios": [{"id": "LOGIN", "parameters": {}}]},
        {"scenarios": [{"id": "LOGIN", "engine": "http"}]},
        {"scenarios": [{"id": "LOGIN"}, {"id": "LOGIN"}]},
        {"scenarios": [{"id": "import.module"}]},
        {"accounts": {"catalog": "accounts.json", "include_ids": ["a", "a"]}},
        {"accounts": {"catalog": "accounts.json", "password": "SENSITIVE_VALUE"}},
        {"browser_profile": "stealth"},
        {"network_profile": "proxy"},
    ],
)
def test_bad_shapes_bounds_and_unsupported_features_fail(
    tmp_path: Path, document: dict[str, object], patch: dict[str, object]
) -> None:
    with pytest.raises(ConfigurationError):
        load_experiment(write_config(tmp_path, document | patch))


@pytest.mark.parametrize(
    "path",
    [
        "../accounts.json",
        "/accounts.json",
        "C:/accounts.json",
        "C:accounts.json",
        "\\\\host\\share\\accounts.json",
        "data\\accounts.json",
        "CON.json",
        "data/NUL.json",
        "data/accounts.json:stream",
        "./accounts.json",
        "data//accounts.json",
        "data./accounts.json",
        "data /accounts.json",
        "accounts;command.json",
        "$(command).json",
        "accounts.txt",
    ],
)
def test_unsafe_catalog_paths_fail(
    tmp_path: Path, document: dict[str, object], path: str
) -> None:
    document["accounts"] = {"catalog": path}
    with pytest.raises(ConfigurationError):
        load_experiment(write_config(tmp_path, document))


@pytest.mark.parametrize("path", ["..", "/tmp/reports", "C:/reports", "AUX", "a/../b"])
def test_unsafe_output_paths_fail(
    tmp_path: Path, document: dict[str, object], path: str
) -> None:
    document["output_dir"] = path
    with pytest.raises(ConfigurationError):
        load_experiment(write_config(tmp_path, document))


@pytest.mark.parametrize(
    ("suffix", "content"),
    [
        (".json", '{"schema_version":1,"schema_version":2}'),
        (".json", '{"seed": NaN}'),
        (".json", "{"),
        (".json", "[]"),
        (".yaml", "---\na: b\n---\na: c\n"),
        (".yaml", "a: 1\na: 2\n"),
        (".yaml", "a: &loop [*loop]\n"),
        (".yaml", '!!python/object/apply:os.system ["SENSITIVE_VALUE"]'),
        (".yaml", "a: 2026-10-28\n"),
        (".yaml", "a: [\n"),
        (".toml", "seed=1"),
        (".json", "[" * 40 + "0" + "]" * 40),
        (".yaml", "[" * 40 + "0" + "]" * 40),
        pytest.param(".json", " " * 65537, id="oversize-json"),
    ],
)
def test_bad_unsafe_or_oversized_documents_are_sanitized(
    tmp_path: Path, suffix: str, content: str
) -> None:
    path = tmp_path / ("bad" + suffix)
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ConfigurationError) as caught:
        load_experiment(path)
    assert "SENSITIVE_VALUE" not in str(caught.value)
    assert "SENSITIVE_VALUE" not in repr(caught.value.issues)


def test_invalid_encoding_and_missing_files_are_classified(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_bytes(b"\xff\xfe\x00")
    with pytest.raises(ConfigurationError):
        load_experiment(path)
    with pytest.raises(ConfigurationError):
        load_experiment(tmp_path / "missing.json")


@pytest.mark.parametrize("origin", ["http://example.com:80", "http://10.0.0.1:80"])
def test_disallowed_origins_are_blocked(
    tmp_path: Path, document: dict[str, object], origin: str
) -> None:
    document["target"] = {"origin": origin}
    with pytest.raises(ScopeViolationError):
        load_experiment(write_config(tmp_path, document))


@pytest.mark.parametrize("blocked", [False, True])
def test_static_validation_opens_only_config_without_outbound_work(
    tmp_path: Path,
    document: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
    blocked: bool,
) -> None:
    if blocked:
        document["target"] = {"origin": "http://example.com:80"}
    path = write_config(tmp_path, document)
    original_open = Path.open
    opened: list[Path] = []

    def guarded_open(self: Path, *args: object, **kwargs: object):
        assert self == path, "Validation attempted to read another file"
        opened.append(self)
        return original_open(self, *args, **kwargs)

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("Validation performed secret/process/network work")

    monkeypatch.setattr(Path, "open", guarded_open)
    monkeypatch.setattr(os, "getenv", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    if blocked:
        with pytest.raises(ScopeViolationError):
            load_experiment(path)
    else:
        load_experiment(path)
    assert opened == [path]
    assert not (tmp_path / "reports").exists()


@pytest.mark.parametrize("selection", ["source", "catalog", "output"])
def test_symlink_or_windows_junction_escape_is_rejected(
    tmp_path: Path, document: dict[str, object], selection: str
) -> None:
    base = tmp_path / "config"
    outside = tmp_path / "outside"
    base.mkdir()
    outside.mkdir()
    link = base / "escape"
    if os.name == "nt":
        script = tmp_path / "make-junction.ps1"
        script.write_text(
            "param([string]$LinkPath, [string]$TargetPath)\n"
            "New-Item -ItemType Junction -Path $LinkPath -Target $TargetPath "
            "-ErrorAction Stop | Out-Null\n",
            encoding="utf-8",
        )
        subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-File",
                str(script),
                str(link),
                str(outside),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=20,
        )
    else:
        link.symlink_to(outside, target_is_directory=True)
    if selection == "source":
        write_config(outside, document)
        path = link / "experiment.json"
    else:
        if selection == "catalog":
            document["accounts"] = {"catalog": "escape/accounts.json"}
        else:
            document["output_dir"] = "escape/reports"
        path = write_config(base, document)
    with pytest.raises(ConfigurationError) as caught:
        load_experiment(path)
    assert caught.value.issues[0].code == "reparse_path_disabled"


@pytest.mark.parametrize(
    "path", ["//host/share/file.yaml", "\\\\host\\file.json", "\\\\?\\C:\\file.yaml"]
)
def test_network_or_device_config_source_is_rejected_before_open(
    path: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("Network/device source must not be opened")

    monkeypatch.setattr(Path, "open", forbidden)
    with pytest.raises(ConfigurationError):
        load_experiment(Path(path))


@pytest.mark.parametrize("suffix", [".yaml", ".json"])
def test_node_budget_rejects_wide_documents(tmp_path: Path, suffix: str) -> None:
    path = tmp_path / ("wide" + suffix)
    path.write_text("[" + ",".join("0" for _ in range(4100)) + "]", encoding="utf-8")
    with pytest.raises(ConfigurationError) as caught:
        load_experiment(path)
    assert caught.value.issues[0].code == "document_complexity_limit"


@pytest.mark.parametrize(
    "patch",
    [
        {"workload": {"users": 3}},
        {"workload": {"spawn_rate": 2}},
        {"workload": {"max_rps": 6}},
        {"workload": {"max_requests": 101}},
        {"workload": {"burst": True}},
        {"workload": {"concurrency": 2}},
        {"accounts": {"catalog": "accounts.json"}},
    ],
)
def test_http_limits_cannot_inherit_browser_fields_or_exceed_smoke_bounds(
    tmp_path: Path, patch: dict[str, object]
) -> None:
    document = json.loads((FIXTURES / "local-http.json").read_text(encoding="utf-8"))
    with pytest.raises(ConfigurationError):
        load_experiment(write_config(tmp_path, document | patch))


def test_seeded_random_delay_and_filter_are_preserved_as_values(
    tmp_path: Path, document: dict[str, object]
) -> None:
    document["think_time"] = {"mode": "seeded_random", "min_s": 3, "max_s": 7}
    document["accounts"] = {
        "catalog": "accounts.json",
        "include_ids": ["test-b", "test-a"],
    }
    document["seed"] = 19
    experiment = load_experiment(write_config(tmp_path, document))
    assert experiment.seed == 19
    assert experiment.think_time.min_s == 3
    assert experiment.think_time.max_s == 7
    assert experiment.accounts is not None
    assert experiment.accounts.include_ids == ("test-b", "test-a")
