"""Real catalog reads validate the entire document without resolving secrets."""

import json
import os
import socket
import subprocess
import traceback
from collections.abc import Iterator, Mapping
from pathlib import Path

import pytest

from web_stress_lab.domain.errors import AccountValidationError
from web_stress_lab.interfaces.accounts import load_accounts
from web_stress_lab.interfaces.configuration import load_experiment

pytestmark = pytest.mark.integration
FIXTURES = Path(__file__).resolve().parents[2] / "fixtures/experiments"


def record(account_id: str) -> dict[str, object]:
    return {
        "account_id": account_id,
        "username": f"synthetic-{account_id}",
        "password_ref": "env:STRESSLAB_TEST_PASSWORD",
    }


def write_catalog(tmp_path: Path, document: object) -> Path:
    path = tmp_path / "accounts.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def test_synthetic_fixture_loads_domain_values_without_secret_values() -> None:
    accounts = load_accounts(FIXTURES / "accounts.synthetic.json")
    assert tuple(item.account_id for item in accounts) == (
        "synthetic-001",
        "synthetic-002",
    )
    assert accounts[0].password_ref == "env:STRESSLAB_TEST_PASSWORD"
    assert accounts[0].totp_secret_ref is None
    assert accounts[1].totp_secret_ref == "env:STRESSLAB_TEST_TOTP_SECRET_2"
    assert accounts[0].network_profile == "direct"
    assert accounts[0].browser_profile == "default"


def test_filter_is_catalog_ordered_and_independent_of_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = write_catalog(
        tmp_path,
        {"schema_version": 1, "accounts": [record("b"), record("a"), record("c")]},
    )
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    selected = load_accounts(path, include_ids=("c", "b"))
    assert tuple(item.account_id for item in selected) == ("b", "c")


def test_unicode_username_is_preserved(tmp_path: Path) -> None:
    row = {**record("unicode"), "username": "người dùng"}
    path = write_catalog(tmp_path, {"schema_version": 1, "accounts": [row]})
    assert load_accounts(path)[0].username == "người dùng"


@pytest.mark.parametrize("include_ids", [("unknown",), ("a", "a"), "ab"])
def test_public_catalog_api_rejects_invalid_selection(
    tmp_path: Path, include_ids: tuple[str, ...]
) -> None:
    path = write_catalog(
        tmp_path, {"schema_version": 1, "accounts": [record("a"), record("b")]}
    )
    with pytest.raises(AccountValidationError):
        load_accounts(path, include_ids=include_ids)


@pytest.mark.parametrize(
    "patch",
    [
        {"account_id": ""},
        {"account_id": "bad/id"},
        {"account_id": "id\n"},
        {"account_id": 1},
        {"username": ""},
        {"username": " "},
        {"username": " leading"},
        {"username": "trailing\u00a0"},
        {"username": "name\nCANARY_PASSWORD"},
        {"username": "name\x00"},
        {"username": "u" * 129},
        {"username": False},
        {"password_ref": "CANARY_PASSWORD"},
        {"password_ref": None},
        {"password_ref": "env:${CANARY_PASSWORD}"},
        {"password_ref": "env:NAME\n"},
        {"totp_secret_ref": "file:CANARY_PASSWORD"},
        {"network_profile": "CANARY_PASSWORD"},
        {"network_profile": {"proxy": "CANARY_PASSWORD"}},
        {"browser_profile": "CANARY_PASSWORD"},
        {"password": "CANARY_PASSWORD"},
        {"totp_secret": "CANARY_PASSWORD"},
        {"CANARY_PASSWORD": "hidden-value"},
    ],
)
def test_bad_metadata_in_excluded_row_cannot_escape_validation(
    tmp_path: Path, patch: dict[str, object]
) -> None:
    excluded = {**record("excluded"), **patch}
    path = write_catalog(
        tmp_path,
        {"schema_version": 1, "accounts": [record("selected"), excluded]},
    )
    with pytest.raises(AccountValidationError) as caught:
        load_accounts(path, include_ids=("selected",))
    diagnostic = "".join(traceback.format_exception(caught.value))
    assert "CANARY_PASSWORD" not in diagnostic
    assert "CANARY_PASSWORD" not in repr(caught.value.issues)
    assert caught.value.exit_code == 2


@pytest.mark.parametrize("missing", ["account_id", "username", "password_ref"])
def test_required_fields_are_not_guessed(tmp_path: Path, missing: str) -> None:
    row = record("first")
    del row[missing]
    path = write_catalog(tmp_path, {"schema_version": 1, "accounts": [row]})
    with pytest.raises(AccountValidationError) as caught:
        load_accounts(path)
    assert any(issue.field == f"accounts.0.{missing}" for issue in caught.value.issues)


@pytest.mark.parametrize(
    "document",
    [
        [record("legacy")],
        {"users": [{"username": "legacy", "password": "CANARY_PASSWORD"}]},
        {"schema_version": 2, "accounts": [record("a")]},
        {"schema_version": True, "accounts": [record("a")]},
        {"schema_version": "1", "accounts": [record("a")]},
        {"schema_version": 1.0, "accounts": [record("a")]},
        {"schema_version": 1, "accounts": []},
        {"schema_version": 1, "accounts": [record(f"a{i}") for i in range(101)]},
        {"schema_version": 1, "accounts": [record("a")], "legacy": True},
    ],
)
def test_legacy_versions_unknown_fields_and_catalog_bounds_fail(
    tmp_path: Path, document: object
) -> None:
    with pytest.raises(AccountValidationError):
        load_accounts(write_catalog(tmp_path, document))


@pytest.mark.parametrize("duplicate", ["account_id", "username"])
def test_duplicate_excluded_rows_are_rejected(tmp_path: Path, duplicate: str) -> None:
    first, second = record("first"), record("second")
    second[duplicate] = first[duplicate]
    path = write_catalog(tmp_path, {"schema_version": 1, "accounts": [first, second]})
    with pytest.raises(AccountValidationError):
        load_accounts(path, include_ids=("first",))


@pytest.mark.parametrize(
    "raw",
    [
        '{"schema_version":1,"schema_version":1,"accounts":[]}',
        '{"CANARY_PASSWORD":',
        '{"schema_version":NaN}',
        " " * 65537,
        "[" * 34 + "0" + "]" * 34,
        "[" + ",".join("0" for _ in range(4097)) + "]",
    ],
    ids=["duplicate-keys", "malformed", "nonfinite", "oversized", "deep", "many-nodes"],
)
def test_reader_failures_are_account_errors_with_redacted_diagnostics(
    tmp_path: Path, raw: str
) -> None:
    path = tmp_path / "accounts.json"
    path.write_text(raw, encoding="utf-8")
    with pytest.raises(AccountValidationError) as caught:
        load_accounts(path)
    assert "CANARY_PASSWORD" not in "".join(traceback.format_exception(caught.value))


def test_catalog_requires_json_and_regular_local_file(tmp_path: Path) -> None:
    for path in (tmp_path / "accounts.yaml", tmp_path / "missing.json", tmp_path):
        with pytest.raises(AccountValidationError):
            load_accounts(path)


def test_invalid_utf8_is_a_sanitized_account_error(tmp_path: Path) -> None:
    path = tmp_path / "accounts.json"
    path.write_bytes(b"CANARY_PASSWORD\xff")
    with pytest.raises(AccountValidationError) as caught:
        load_accounts(path)
    assert "CANARY_PASSWORD" not in "".join(traceback.format_exception(caught.value))


def test_catalog_path_rechecks_native_link_components(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    write_catalog(real, {"schema_version": 1, "accounts": [record("a")]})
    linked = tmp_path / "linked"
    if os.name == "nt":
        subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(linked), str(real)],
            check=True,
            capture_output=True,
        )
    else:
        linked.symlink_to(real, target_is_directory=True)
    with pytest.raises(AccountValidationError) as caught:
        load_accounts(linked / "accounts.json")
    assert caught.value.issues[0].code == "reparse_path_disabled"


def test_catalog_validation_has_no_secret_network_process_or_output_effects(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = write_catalog(tmp_path, {"schema_version": 1, "accounts": [record("a")]})
    opened = []
    original_open = Path.open

    def deny(*args: object, **kwargs: object) -> None:
        raise AssertionError("Unexpected execution side effect")

    class NoEnvironment(Mapping[str, str]):
        def __getitem__(self, key: str) -> str:
            raise AssertionError("Unexpected environment lookup")

        def __iter__(self) -> Iterator[str]:
            raise AssertionError("Unexpected environment enumeration")

        def __len__(self) -> int:
            raise AssertionError("Unexpected environment access")

    def only_catalog(self: Path, *args: object, **kwargs: object):
        assert self == path
        opened.append(self)
        return original_open(self, *args, **kwargs)

    with monkeypatch.context() as guarded:
        guarded.setattr(os, "environ", NoEnvironment())
        guarded.setattr(socket, "socket", deny)
        guarded.setattr(subprocess, "Popen", deny)
        guarded.setattr(Path, "open", only_catalog)
        assert len(load_accounts(path)) == 1
    assert opened == [path]
    assert list(tmp_path.iterdir()) == [path]


def test_static_experiment_validation_does_not_read_bad_catalog(tmp_path: Path) -> None:
    fixture = tmp_path / "experiment.yaml"
    fixture.write_bytes((FIXTURES / "local-browser.yaml").read_bytes())
    (tmp_path / "accounts.synthetic.json").write_text("not JSON", encoding="utf-8")
    assert load_experiment(fixture).accounts is not None
