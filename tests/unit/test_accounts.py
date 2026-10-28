"""Identity selection and explicit reference rules stay independent of adapters."""

from dataclasses import FrozenInstanceError, replace

import pytest

from web_stress_lab.domain.accounts import Account, environment_name, select_accounts
from web_stress_lab.domain.errors import AccountValidationError

pytestmark = pytest.mark.unit


def account(account_id: str) -> Account:
    return Account(account_id, f"synthetic-{account_id}", "env:STRESSLAB_TEST_PASSWORD")


def test_accounts_are_immutable_and_repr_omits_identity_and_references() -> None:
    identity = account("first")
    with pytest.raises(FrozenInstanceError):
        identity.username = "changed"
    assert identity.username not in repr(identity)
    assert identity.password_ref not in repr(identity)
    assert identity.network_profile == "direct"
    assert identity.browser_profile == "default"
    assert identity.totp_secret_ref is None


def test_selection_preserves_catalog_order_and_empty_filter_selects_all() -> None:
    catalog = (account("third"), account("first"), account("second"))
    assert select_accounts(catalog) == catalog
    selected = select_accounts(catalog, ("second", "third"))
    assert tuple(item.account_id for item in selected) == ("third", "second")


@pytest.mark.parametrize(
    ("include_ids", "code"),
    [
        (("missing",), "unknown_account_id"),
        (("first", "first"), "duplicate_filter_id"),
        (("first",) * 101, "invalid_filter"),
        ((False,), "invalid_filter"),
    ],
)
def test_invalid_filters_are_classified_without_echoing_ids(
    include_ids: tuple[str, ...], code: str
) -> None:
    with pytest.raises(AccountValidationError) as caught:
        select_accounts((account("first"),), include_ids)
    assert caught.value.issues[0].code == code
    assert "missing" not in str(caught.value)


@pytest.mark.parametrize("include_ids", ["ab", None, ["a"]])
def test_filter_requires_the_typed_id_tuple(include_ids: tuple[str, ...]) -> None:
    with pytest.raises(AccountValidationError) as caught:
        select_accounts((account("a"), account("b")), include_ids)
    assert caught.value.issues[0].code == "invalid_filter"


@pytest.mark.parametrize("duplicate", ["account_id", "username"])
def test_filter_cannot_hide_duplicate_identities(duplicate: str) -> None:
    first, second = account("first"), account("second")
    if duplicate == "account_id":
        second = replace(second, account_id=first.account_id)
    else:
        second = replace(second, username=first.username)
    with pytest.raises(AccountValidationError, match="Invalid account"):
        select_accounts((first, second), ("first",))


@pytest.mark.parametrize("name", ["STRESSLAB_TEST_PASSWORD", "_PRIVATE", "Mixed_01"])
def test_environment_names_are_explicit(name: str) -> None:
    assert environment_name(f"env:{name}") == name


@pytest.mark.parametrize(
    "reference",
    [
        "STRESSLAB_TEST_PASSWORD",
        "plaintext-secret",
        "env:",
        "env:1PASSWORD",
        "env:NAME\n",
        "env: NAME",
        "env:NAME/subpath",
        "env:${NAME}",
        "file:credentials.json",
        "https://example.invalid/secret",
        "ENV:NAME",
        "env:" + "A" * 129,
        "env:mật_khẩu",
        None,
    ],
)
def test_malformed_reference_is_rejected_before_environment_access(
    reference: str,
) -> None:
    with pytest.raises(AccountValidationError) as caught:
        environment_name(reference)
    assert caught.value.issues[0].code == "invalid_secret_reference"
    assert caught.value.exit_code == 2
