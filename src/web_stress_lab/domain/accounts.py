"""Immutable identity metadata and deterministic selection; no secret values."""

import re
from dataclasses import dataclass, field
from typing import Literal

from web_stress_lab.domain.errors import AccountValidationError, InputIssue

MAX_ACCOUNTS = 100
type NetworkProfile = Literal["direct"]
type BrowserProfile = Literal["default"]
_ENV_REFERENCE = re.compile(r"env:([A-Za-z_][A-Za-z0-9_]{0,127})")


@dataclass(frozen=True)
class Account:
    account_id: str
    username: str = field(repr=False)
    password_ref: str = field(repr=False)
    totp_secret_ref: str | None = field(default=None, repr=False)
    network_profile: NetworkProfile = "direct"
    browser_profile: BrowserProfile = "default"


def environment_name(reference: str) -> str:
    match = _ENV_REFERENCE.fullmatch(reference) if isinstance(reference, str) else None
    if match is None:
        raise AccountValidationError(
            [InputIssue("secret_ref", "invalid_secret_reference")]
        )
    return match.group(1)


def select_accounts(
    accounts: tuple[Account, ...], include_ids: tuple[str, ...] = ()
) -> tuple[Account, ...]:
    ids = {item.account_id for item in accounts}
    if len(ids) != len(accounts):
        raise AccountValidationError([InputIssue("accounts", "duplicate_account_id")])
    if len({item.username for item in accounts}) != len(accounts):
        raise AccountValidationError([InputIssue("accounts", "duplicate_username")])
    if (
        not isinstance(include_ids, tuple)
        or len(include_ids) > MAX_ACCOUNTS
        or any(not isinstance(item, str) for item in include_ids)
    ):
        raise AccountValidationError(
            [InputIssue("accounts.include_ids", "invalid_filter")]
        )
    selected = set(include_ids)
    if len(selected) != len(include_ids):
        raise AccountValidationError(
            [InputIssue("accounts.include_ids", "duplicate_filter_id")]
        )
    if not selected <= ids:
        raise AccountValidationError(
            [InputIssue("accounts.include_ids", "unknown_account_id")]
        )
    return tuple(
        item for item in accounts if not selected or item.account_id in selected
    )
