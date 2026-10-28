"""Resolve only explicitly named process-environment variables."""

import os

from web_stress_lab.application.ports import SecretProvider
from web_stress_lab.domain.accounts import environment_name
from web_stress_lab.domain.errors import AccountValidationError, InputIssue


class EnvironmentSecretProvider(SecretProvider):
    def resolve(self, reference: str) -> str:
        value = os.environ.get(environment_name(reference))
        if value is None or value == "":
            raise AccountValidationError(
                [InputIssue("secret_ref", "secret_unavailable")]
            )
        return value
