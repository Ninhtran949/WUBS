"""Pure scope/timing rules cannot authorize external or unregistered work."""

import pytest

from web_stress_lab.domain.errors import ConfigurationError, ScopeViolationError
from web_stress_lab.domain.policy import check_scope, check_timing

pytestmark = pytest.mark.unit
LOCAL = "http://127.0.0.1:8765"


@pytest.mark.parametrize(
    ("origin", "expected"),
    [
        (LOCAL, LOCAL),
        (LOCAL + "/", LOCAL),
        ("HTTP://127.0.0.1:08765/", LOCAL),
        ("https://[::1]:9443/", "https://[::1]:9443"),
    ],
)
def test_exact_local_origin_normalization(origin: str, expected: str) -> None:
    actual, allowed = check_scope(
        "local_lab", "browser", origin, [origin], ["LOGIN"], ["LOGIN"]
    )
    assert actual == expected
    assert allowed == (expected,)


@pytest.mark.parametrize(
    "origin",
    [
        "http://localhost:8765",
        "http://127.0.0.2:8765",
        "http://example.com:80",
        "http://169.254.169.254:80",
        "http://10.0.0.1:80",
        "http://[::]:8765",
    ],
)
def test_non_lab_hosts_are_blocked_without_dns(origin: str) -> None:
    with pytest.raises(ScopeViolationError):
        check_scope("local_lab", "browser", origin, [origin], ["LOGIN"], ["LOGIN"])


@pytest.mark.parametrize(
    "origin",
    [
        "file:///tmp/data",
        "ftp://127.0.0.1:8765",
        "http://127.0.0.1",
        "http://127.0.0.1:0",
        "http://127.0.0.1:65536",
        "http://127.0.0.1:bad",
        "http://user:SECRET@127.0.0.1:8765",
        LOCAL + "/login",
        LOCAL + "?",
        LOCAL + "#",
        LOCAL + "\n",
        "http://*:8765",
        "http://[::1:8765",
        " http://127.0.0.1:8765",
    ],
)
def test_malformed_or_unsafe_origins_are_configuration_errors(origin: str) -> None:
    with pytest.raises(ConfigurationError) as caught:
        check_scope("local_lab", "browser", origin, [origin], ["LOGIN"], ["LOGIN"])
    assert "SECRET" not in str(caught.value)


@pytest.mark.parametrize("mode", ["owned_staging", "external_read_only"])
def test_external_declarations_do_not_establish_authorization(mode: str) -> None:
    with pytest.raises(ScopeViolationError):
        check_scope(mode, "browser", LOCAL, [LOCAL], ["LOGIN"], ["LOGIN"])


def test_scope_cannot_include_another_loopback_service() -> None:
    with pytest.raises(ScopeViolationError):
        check_scope(
            "local_lab",
            "browser",
            LOCAL,
            [LOCAL, "http://127.0.0.1:9000"],
            ["LOGIN"],
            ["LOGIN"],
        )


@pytest.mark.parametrize(
    ("selected", "permitted", "origins", "category"),
    [
        (["LOGIN", "LOGIN"], ["LOGIN"], [LOCAL], ConfigurationError),
        (["UNKNOWN"], ["LOGIN"], [LOCAL], ConfigurationError),
        (["LOGIN"], ["UNKNOWN"], [LOCAL], ConfigurationError),
        (["LOGIN"], ["LOGIN", "LOGIN"], [LOCAL], ConfigurationError),
        (["LOGIN"], ["LOGIN"], [LOCAL, LOCAL + "/"], ConfigurationError),
        (["HTTP_HEALTH"], ["HTTP_HEALTH"], [LOCAL], ConfigurationError),
        (["LOGIN"], [], [LOCAL], ScopeViolationError),
    ],
)
def test_registered_unique_scenarios_and_explicit_capabilities(
    selected: list[str],
    permitted: list[str],
    origins: list[str],
    category: type[ConfigurationError],
) -> None:
    with pytest.raises(category):
        check_scope("local_lab", "browser", LOCAL, origins, selected, permitted)


def test_http_contract_is_distinct_from_browser() -> None:
    assert (
        check_scope(
            "local_lab", "http", LOCAL, [LOCAL], ["HTTP_HEALTH"], ["HTTP_HEALTH"]
        )[0]
        == LOCAL
    )


@pytest.mark.parametrize(
    ("duration", "shutdown", "operation", "minimum", "maximum"),
    [(10, 30, 15, 0, 0), (60, 19, 15, 0, 0), (60, 30, 15, 7, 3), (60, 30, 15, 0, 61)],
)
def test_incompatible_time_budgets_are_rejected(
    duration: float,
    shutdown: float,
    operation: float,
    minimum: float,
    maximum: float,
) -> None:
    with pytest.raises(ConfigurationError):
        check_timing(duration, shutdown, operation, minimum, maximum)


def test_shutdown_covers_operation_and_cleanup_reserve() -> None:
    check_timing(60, 20, 15, 3, 7)
