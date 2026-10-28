"""Static local scope and compatible time budgets, without execution or I/O."""

from collections.abc import Mapping, Sequence
from types import MappingProxyType
from typing import Literal
from urllib.parse import urlsplit

from web_stress_lab.domain.errors import (
    ConfigurationError,
    InputIssue,
    ScopeViolationError,
)

type Engine = Literal["browser", "http"]

SCENARIO_ENGINES: Mapping[str, Engine] = MappingProxyType(
    {"LOGIN": "browser", "HTTP_HEALTH": "http"}
)
CLEANUP_RESERVE_S = 5.0


def _origin(value: str, field: str) -> str:
    invalid = InputIssue(field, "invalid_origin")
    if any(ord(char) <= 32 or ord(char) == 127 for char in value) or any(
        char in value for char in "\\*?#"
    ):
        raise ConfigurationError([invalid])
    try:
        url = urlsplit(value)
        host, port = url.hostname, url.port
        if (
            url.scheme not in {"http", "https"}
            or url.username is not None
            or url.password is not None
            or not host
            or port is None
            or not 1 <= port <= 65535
            or url.path not in {"", "/"}
        ):
            raise ConfigurationError([invalid])
    except ValueError:
        raise ConfigurationError([invalid]) from None
    if host not in {"127.0.0.1", "::1"}:
        raise ScopeViolationError([InputIssue(field, "external_origin_disabled")])
    authority = f"[{host}]" if ":" in host else host
    return f"{url.scheme}://{authority}:{port}"


def _unique(values: Sequence[str], field: str) -> None:
    if len(values) != len(set(values)):
        raise ConfigurationError([InputIssue(field, "duplicate_value")])


def check_scope(
    mode: str,
    engine: Engine,
    origin: str,
    allowed_origins: Sequence[str],
    scenarios: Sequence[str],
    allowed_scenarios: Sequence[str],
) -> tuple[str, tuple[str, ...]]:
    if mode != "local_lab":
        raise ScopeViolationError([InputIssue("target.mode", "external_mode_disabled")])
    normalized = _origin(origin, "target.origin")
    origins = tuple(
        _origin(value, "scope.allowed_origins") for value in allowed_origins
    )
    _unique(origins, "scope.allowed_origins")
    if set(origins) != {normalized}:
        raise ScopeViolationError(
            [InputIssue("scope.allowed_origins", "local_target_scope_mismatch")]
        )
    for field, values in (
        ("scenarios", scenarios),
        ("scope.allowed_scenarios", allowed_scenarios),
    ):
        _unique(values, field)
        for value in values:
            if value not in SCENARIO_ENGINES:
                raise ConfigurationError([InputIssue(field, "unknown_scenario")])
            if SCENARIO_ENGINES[value] != engine:
                raise ConfigurationError(
                    [InputIssue(field, "scenario_engine_mismatch")]
                )
    if not set(scenarios).issubset(allowed_scenarios):
        raise ScopeViolationError(
            [InputIssue("scope.allowed_scenarios", "scenario_not_allowed")]
        )
    return normalized, origins


def check_timing(
    duration_s: float,
    shutdown_s: float,
    operation_s: float,
    think_min_s: float,
    think_max_s: float,
) -> None:
    if operation_s > duration_s:
        raise ConfigurationError(
            [InputIssue("limits.max_duration_s", "operation_exceeds_duration")]
        )
    if shutdown_s < operation_s + CLEANUP_RESERVE_S:
        raise ConfigurationError(
            [InputIssue("limits.shutdown_timeout_s", "shutdown_budget")]
        )
    if think_min_s > think_max_s:
        raise ConfigurationError([InputIssue("think_time", "invalid_delay_range")])
    if think_max_s > duration_s:
        raise ConfigurationError([InputIssue("think_time", "delay_exceeds_duration")])
