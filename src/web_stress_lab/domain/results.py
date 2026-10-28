"""Immutable outcomes and partial-run accounting without storage or engine code."""

import math
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal

from web_stress_lab.domain.errors import InputIssue, ReportingError
from web_stress_lab.domain.policy import SCENARIO_ENGINES, Engine

type CaseStatus = Literal["COMPLETED", "FAILED", "BLOCKED", "CANCELLED", "NOT_RUN"]
type RunStatus = Literal["RUNNING", "COMPLETED", "FAILED", "BLOCKED", "CANCELLED", "INTERRUPTED"]
type ErrorCategory = Literal[
    "ConfigurationError", "AccountValidationError", "AuthenticationError", "TOTPError",
    "ProxyConnectionError", "NavigationTimeoutError", "LocatorTimeoutError",
    "BrowserCrashError", "ScenarioAssertionError", "ResourceLimitError",
    "ScopeViolationError", "ReportingError",
]
CASE_STATUSES: tuple[CaseStatus, ...] = ("COMPLETED", "FAILED", "BLOCKED", "CANCELLED", "NOT_RUN")
RUN_STATUSES: tuple[RunStatus, ...] = (
    "RUNNING",
    "COMPLETED",
    "FAILED",
    "BLOCKED",
    "CANCELLED",
    "INTERRUPTED",
)


def _failure(code: str) -> ReportingError:
    return ReportingError([InputIssue("$", code)])


def _aware(value: datetime) -> bool:
    return isinstance(value, datetime) and value.utcoffset() is not None


def _utc_aware(value: datetime) -> bool:
    return isinstance(value, datetime) and value.utcoffset() == timedelta(0)


@dataclass(frozen=True)
class CaseOutcome:
    case_id: str
    scenario_id: str
    status: CaseStatus
    started_at: datetime | None
    finished_at: datetime
    duration_s: float | None
    error_category: ErrorCategory | None = None
    effect: Literal["confirmed", "unknown"] = "confirmed"
    attempt: int = 1
    account_ref: str | None = None
    duration_unavailable_reason: Literal["not_started", "not_measured"] | None = None
    schema_version: int = 1
    data_source: Literal["synthetic"] = "synthetic"

    def __post_init__(self) -> None:
        if not _utc_aware(self.finished_at) or self.status not in CASE_STATUSES:
            raise _failure("invalid_case_state")
        if self.status in {"FAILED", "BLOCKED"} and self.error_category is None:
            raise _failure("missing_error_category")
        if self.status == "COMPLETED" and (
            self.effect != "confirmed" or self.error_category is not None
        ):
            raise _failure("invalid_success_state")
        if self.started_at is None:
            if (self.status not in {"NOT_RUN", "CANCELLED"} or self.attempt != 0
                or self.duration_s is not None or self.duration_unavailable_reason != "not_started"):
                raise _failure("invalid_not_started_state")
        elif (not _utc_aware(self.started_at) or self.finished_at < self.started_at
              or self.status == "NOT_RUN" or type(self.attempt) is not int or not 1 <= self.attempt <= 2):
            raise _failure("invalid_case_timing")
        if self.duration_s is None:
            expected = "not_started" if self.started_at is None else "not_measured"
            if self.duration_unavailable_reason != expected:
                raise _failure("missing_measurement_reason")
        elif (type(self.duration_s) not in {int, float} or not math.isfinite(self.duration_s)
              or self.duration_s < 0 or self.duration_unavailable_reason is not None):
            raise _failure("invalid_duration")


@dataclass(frozen=True)
class RunManifest:
    run_id: str
    engine: Engine
    origin: str
    seed: int
    planned_cases: int
    started_at: datetime
    python_version: str
    package_version: str
    os_name: str
    status: RunStatus = "RUNNING"
    finished_at: datetime | None = None
    reporting_complete: bool = False
    reporting_error: Literal["finalization_failed"] | None = None
    schema_version: int = 1
    data_source: Literal["synthetic"] = "synthetic"

    def __post_init__(self) -> None:
        if self.status not in RUN_STATUSES:
            raise _failure("invalid_manifest")
        if (not _utc_aware(self.started_at) or type(self.planned_cases) is not int
            or not 1 <= self.planned_cases <= 100):
            raise _failure("invalid_manifest")
        if self.status == "RUNNING":
            if self.finished_at is not None or self.reporting_complete or self.reporting_error:
                raise _failure("invalid_initial_manifest")
        elif (self.finished_at is None or not _utc_aware(self.finished_at)
              or self.finished_at < self.started_at):
            raise _failure("invalid_final_manifest")
        if self.reporting_error and (self.status != "FAILED" or self.reporting_complete):
            raise _failure("invalid_reporting_failure")


@dataclass(frozen=True)
class RunReport:
    manifest: RunManifest
    cases: tuple[CaseOutcome, ...]


def check_cases(manifest: RunManifest, cases: tuple[CaseOutcome, ...]) -> None:
    if len(cases) > manifest.planned_cases or len({item.case_id for item in cases}) != len(cases):
        raise _failure("duplicate_or_excess_cases")
    for item in cases:
        if SCENARIO_ENGINES.get(item.scenario_id) != manifest.engine:
            raise _failure("scenario_engine_mismatch")
        if (item.finished_at < manifest.started_at
            or (item.started_at is not None and item.started_at < manifest.started_at)
            or (manifest.finished_at is not None and item.finished_at > manifest.finished_at)):
            raise _failure("case_outside_run")


def check_completion(
    manifest: RunManifest, cases: tuple[CaseOutcome, ...], status: RunStatus
) -> None:
    check_cases(manifest, cases)
    if status not in RUN_STATUSES or status == "RUNNING":
        raise _failure("terminal_status_required")
    if status == "COMPLETED" and (
        len(cases) != manifest.planned_cases or any(item.status != "COMPLETED" for item in cases)
    ):
        raise _failure("incomplete_success")


def summarize(report: RunReport) -> dict[str, object]:
    run, cases = report.manifest, report.cases
    return {
        "schema_version": 1, "run_id": run.run_id, "data_source": run.data_source,
        "status": run.status, "reporting_complete": run.reporting_complete,
        "reporting_error": run.reporting_error, "planned_cases": run.planned_cases,
        "recorded_cases": len(cases), "unrecorded_cases": run.planned_cases - len(cases),
        "counts": {status: sum(item.status == status for item in cases) for status in CASE_STATUSES},
        "duration_available": sum(item.duration_s is not None for item in cases),
        "duration_unavailable": sum(item.duration_s is None for item in cases),
        "unknown_effect_cases": sum(item.effect == "unknown" for item in cases),
    }
