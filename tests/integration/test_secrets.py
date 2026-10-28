"""Exercise the real environment adapter without real credentials or fallback I/O."""

import logging
import os
import traceback
from collections.abc import Iterator, Mapping

import pytest

from web_stress_lab.application.ports import SecretProvider
from web_stress_lab.domain.errors import AccountValidationError
from web_stress_lab.infrastructure.secrets import EnvironmentSecretProvider

pytestmark = pytest.mark.integration


class EnvironmentProbe(Mapping[str, str]):
    def __init__(self) -> None:
        self.lookups: list[str] = []

    def __getitem__(self, key: str) -> str:
        self.lookups.append(key)
        if key == "STRESSLAB_TEST_PASSWORD":
            return "SYNTHETIC_VALUE_CANARY"
        raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        raise AssertionError("Environment enumeration is forbidden")

    def __len__(self) -> int:
        raise AssertionError("Environment enumeration is forbidden")


def test_port_adapter_reads_exactly_one_explicit_variable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider: SecretProvider = EnvironmentSecretProvider()
    environment = EnvironmentProbe()
    with monkeypatch.context() as guarded:
        guarded.setattr(os, "environ", environment)
        value = provider.resolve("env:STRESSLAB_TEST_PASSWORD")
    assert value == "SYNTHETIC_VALUE_CANARY"
    assert environment.lookups == ["STRESSLAB_TEST_PASSWORD"]
    assert value not in repr(provider)


@pytest.mark.parametrize(
    "reference",
    [
        "STRESSLAB_TEST_PASSWORD",
        "SYNTHETIC_VALUE_CANARY",
        "env:${STRESSLAB_TEST_PASSWORD}",
        "file:STRESSLAB_TEST_PASSWORD",
        "env:STRESSLAB_TEST_PASSWORD\n",
        None,
    ],
)
def test_invalid_reference_never_queries_environment(
    reference: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    environment = EnvironmentProbe()
    with monkeypatch.context() as guarded:
        guarded.setattr(os, "environ", environment)
        with pytest.raises(AccountValidationError) as caught:
            EnvironmentSecretProvider().resolve(reference)
    assert environment.lookups == []
    assert caught.value.issues[0].code == "invalid_secret_reference"


@pytest.mark.parametrize("value", [None, ""])
def test_missing_or_empty_variable_is_sanitized(
    value: str | None, monkeypatch: pytest.MonkeyPatch
) -> None:
    variable = "STRESSLAB_SENSITIVE_VARIABLE_CANARY"
    if value is None:
        monkeypatch.delenv(variable, raising=False)
    else:
        monkeypatch.setenv(variable, value)
    with pytest.raises(AccountValidationError) as caught:
        EnvironmentSecretProvider().resolve(f"env:{variable}")
    assert caught.value.issues[0].code == "secret_unavailable"
    diagnostic = "".join(traceback.format_exception(caught.value))
    assert variable not in diagnostic + repr(caught.value.issues)


def test_values_are_not_trimmed_or_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = EnvironmentSecretProvider()
    variable = "STRESSLAB_TEST_PASSWORD"
    monkeypatch.setenv(variable, " first synthetic value ")
    assert provider.resolve(f"env:{variable}") == " first synthetic value "
    monkeypatch.setenv(variable, "second synthetic value")
    assert provider.resolve(f"env:{variable}") == "second synthetic value"
    monkeypatch.delenv(variable)
    with pytest.raises(AccountValidationError):
        provider.resolve(f"env:{variable}")


def test_success_and_failures_do_not_emit_credentials(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    variable, value = "STRESSLAB_VARIABLE_CANARY", "SYNTHETIC_VALUE_CANARY"
    provider = EnvironmentSecretProvider()
    monkeypatch.setenv(variable, value)
    with caplog.at_level(logging.DEBUG):
        assert provider.resolve(f"env:{variable}") == value
        monkeypatch.delenv(variable)
        with pytest.raises(AccountValidationError) as caught:
            provider.resolve(f"env:{variable}")
        logging.getLogger(__name__).error("Credential failure: %s", caught.value)
    output = capsys.readouterr()
    diagnostic = output.out + output.err + caplog.text + repr(provider)
    assert variable not in diagnostic
    assert value not in diagnostic
