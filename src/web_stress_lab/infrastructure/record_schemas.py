"""Strict versioned storage boundary; no schema models cross into the domain."""

import json
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, ValidationError

from web_stress_lab.domain.errors import InputIssue, ReportingError
from web_stress_lab.domain.policy import Engine
from web_stress_lab.domain.results import CaseOutcome, CaseStatus, ErrorCategory, RunManifest, RunStatus

RUN_ID_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$"
type Identifier = Annotated[str, Field(pattern=RUN_ID_PATTERN)]


class _Record(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", allow_inf_nan=False)
    schema_version: Annotated[int, Field(ge=1, le=1)]
    data_source: Literal["synthetic"]


class ManifestRecord(_Record):
    run_id: Identifier
    engine: Engine
    origin: Annotated[str, Field(min_length=1, max_length=2048)]
    seed: Annotated[int, Field(ge=0, le=2**63-1)]
    planned_cases: Annotated[int, Field(ge=1, le=100)]
    started_at: AwareDatetime
    python_version: Annotated[str, Field(min_length=1, max_length=128)]
    package_version: Annotated[str, Field(min_length=1, max_length=128)]
    os_name: Annotated[str, Field(min_length=1, max_length=128)]
    status: RunStatus
    finished_at: AwareDatetime | None
    reporting_complete: bool
    reporting_error: Literal["finalization_failed"] | None

    def manifest(self) -> RunManifest:
        return RunManifest(
            self.run_id, self.engine, self.origin, self.seed, self.planned_cases,
            self.started_at, self.python_version, self.package_version, self.os_name,
            self.status, self.finished_at, self.reporting_complete, self.reporting_error,
            self.schema_version, self.data_source,
        )


class CaseRecord(_Record):
    run_id: Identifier
    case_id: Identifier
    scenario_id: Annotated[str, Field(pattern=r"^[A-Z][A-Z0-9_]{0,63}$")]
    status: CaseStatus
    started_at: AwareDatetime | None
    finished_at: AwareDatetime
    duration_s: Annotated[float, Field(ge=0)] | None
    error_category: ErrorCategory | None
    effect: Literal["confirmed", "unknown"]
    attempt: Annotated[int, Field(ge=0, le=2)]
    account_ref: Annotated[str, Field(pattern=r"^acct_[0-9a-f]{32}$")] | None
    duration_unavailable_reason: Literal["not_started", "not_measured"] | None

    def outcome(self) -> CaseOutcome:
        return CaseOutcome(
            self.case_id, self.scenario_id, self.status, self.started_at,
            self.finished_at, self.duration_s, self.error_category, self.effect,
            self.attempt, self.account_ref, self.duration_unavailable_reason,
            self.schema_version, self.data_source,
        )


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_key")
        result[key] = value
    return result


def _nonfinite(value: str) -> object:
    raise ValueError("nonfinite_number")


def read_json(data: bytes) -> object:
    try:
        result: object = json.loads(data, object_pairs_hook=_unique, parse_constant=_nonfinite)
        return result
    except (ValueError, UnicodeError, RecursionError):
        raise ReportingError([InputIssue("$", "malformed_record")]) from None


def manifest_from_json(data: bytes) -> RunManifest:
    read_json(data)
    try:
        return ManifestRecord.model_validate_json(data).manifest()
    except ValidationError:
        raise ReportingError([InputIssue("$", "invalid_manifest")]) from None


def case_from_json(data: bytes, run_id: str) -> CaseOutcome:
    read_json(data)
    try:
        record = CaseRecord.model_validate_json(data)
    except ValidationError:
        raise ReportingError([InputIssue("$", "invalid_case_record")]) from None
    if record.run_id != run_id:
        raise ReportingError([InputIssue("$", "run_id_mismatch")])
    return record.outcome()
