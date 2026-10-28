"""Errors expose fixed codes and field locations, never rejected input values."""

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class InputIssue:
    field: str
    code: str


class ConfigurationError(Exception):
    message = "Invalid experiment configuration."
    exit_code = 2

    def __init__(self, issues: Sequence[InputIssue]) -> None:
        self.issues = tuple(issues)
        super().__init__(self.message)


class ScopeViolationError(ConfigurationError):
    message = "Experiment scope is blocked."
    exit_code = 3


class AccountValidationError(ConfigurationError):
    message = "Invalid account catalog or secret reference."


class ReportingError(Exception):
    message = "Run reporting failed."
    exit_code = 4

    def __init__(self, issues: Sequence[InputIssue]) -> None:
        self.issues = tuple(issues)
        super().__init__(self.message)
