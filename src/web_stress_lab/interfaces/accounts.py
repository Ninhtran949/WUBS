"""Strict JSON account boundary; metadata validation never resolves credentials."""

from pathlib import Path
from typing import Annotated

from pydantic import Field, ValidationError, field_validator

from web_stress_lab.domain.accounts import (
    MAX_ACCOUNTS,
    Account,
    BrowserProfile,
    NetworkProfile,
    environment_name,
    select_accounts,
)
from web_stress_lab.domain.errors import (
    AccountValidationError,
    ConfigurationError,
    InputIssue,
)
from web_stress_lab.interfaces.configuration import Identifier, InputModel
from web_stress_lab.interfaces.configuration_files import read_document


class AccountInput(InputModel):
    account_id: Identifier
    username: Annotated[str, Field(min_length=1, max_length=128)]
    password_ref: str
    totp_secret_ref: str | None = None
    network_profile: NetworkProfile = "direct"
    browser_profile: BrowserProfile = "default"

    @field_validator("username")
    @classmethod
    def valid_username(cls, value: str) -> str:
        if value != value.strip() or any(
            ord(char) < 32 or ord(char) == 127 for char in value
        ):
            raise ValueError("invalid_username")
        return value


class CatalogInput(InputModel):
    schema_version: Annotated[int, Field(ge=1, le=1)]
    accounts: Annotated[
        list[AccountInput], Field(min_length=1, max_length=MAX_ACCOUNTS)
    ]


_FIELDS = {"schema_version", "accounts"} | set(AccountInput.model_fields)


def load_accounts(
    path: Path, *, include_ids: tuple[str, ...] = ()
) -> tuple[Account, ...]:
    if path.suffix.lower() != ".json":
        raise AccountValidationError([InputIssue("$", "catalog_requires_json")])
    try:
        document, _ = read_document(path)
    except ConfigurationError as error:
        raise AccountValidationError(error.issues) from None
    try:
        parsed = CatalogInput.model_validate(document)
    except ValidationError as error:
        issues = []
        for detail in error.errors(
            include_input=False, include_context=False, include_url=False
        ):
            location = (
                ".".join(
                    str(part) if isinstance(part, int) or part in _FIELDS else "?"
                    for part in detail["loc"]
                )
                or "$"
            )
            issues.append(InputIssue(location, detail["type"]))
        raise AccountValidationError(issues) from None
    accounts = []
    for index, item in enumerate(parsed.accounts):
        for name, reference in (
            ("password_ref", item.password_ref),
            ("totp_secret_ref", item.totp_secret_ref),
        ):
            if reference is not None:
                try:
                    environment_name(reference)
                except AccountValidationError:
                    raise AccountValidationError(
                        [
                            InputIssue(
                                f"accounts.{index}.{name}", "invalid_secret_reference"
                            )
                        ]
                    ) from None
        accounts.append(
            Account(
                item.account_id,
                item.username,
                item.password_ref,
                item.totp_secret_ref,
                item.network_profile,
                item.browser_profile,
            )
        )
    return select_accounts(tuple(accounts), include_ids)
