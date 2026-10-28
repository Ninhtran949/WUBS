"""Counts and completion rules never convert missing observations to success."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta, timezone

import pytest

from web_stress_lab.domain.errors import ReportingError
from web_stress_lab.domain.results import (
    CaseOutcome,
    RunManifest,
    RunReport,
    check_completion,
    summarize,
)

pytestmark = pytest.mark.unit
NOW = datetime(2026, 10, 28, tzinfo=UTC)


def manifest() -> RunManifest:
    return RunManifest("synthetic-run", "browser", "http://127.0.0.1:8765", 0, 2,
                       NOW, "3.12", "0.1.0", "Windows")


def outcome(case_id: str) -> CaseOutcome:
    return CaseOutcome(case_id, "LOGIN", "COMPLETED", NOW, NOW, 0.25)


def test_partial_summary_preserves_missing_case_and_measurement_counts() -> None:
    missing_duration = replace(outcome("a"), duration_s=None,
                               duration_unavailable_reason="not_measured")
    summary = summarize(RunReport(manifest(), (missing_duration,)))
    assert summary["data_source"] == "synthetic"
    assert summary["status"] == "RUNNING"
    assert summary["reporting_complete"] is False
    assert summary["recorded_cases"] == 1
    assert summary["unrecorded_cases"] == 1
    assert summary["duration_available"] == 0
    assert summary["duration_unavailable"] == 1


def test_completed_requires_all_planned_confirmed_successes() -> None:
    run = manifest()
    check_completion(run, (outcome("a"), outcome("b")), "COMPLETED")
    with pytest.raises(ReportingError):
        check_completion(run, (outcome("a"),), "COMPLETED")
    failure = replace(outcome("b"), status="FAILED",
                      error_category="NavigationTimeoutError", effect="unknown")
    with pytest.raises(ReportingError):
        check_completion(run, (outcome("a"), failure), "COMPLETED")
    check_completion(run, (outcome("a"), failure), "FAILED")
    summary = summarize(RunReport(run, (outcome("a"), failure)))
    assert summary["unknown_effect_cases"] == 1
    assert summary["counts"]["FAILED"] == 1


@pytest.mark.parametrize("duration", [-1, float("nan"), float("inf"), True])
def test_invalid_durations_cannot_be_observations(duration: float) -> None:
    with pytest.raises(ReportingError):
        replace(outcome("a"), duration_s=duration)


@pytest.mark.parametrize("change", [
    {"started_at": NOW.replace(tzinfo=None)},
    {"finished_at": NOW - timedelta(seconds=1)},
    {"duration_s": None},
    {"status": "FAILED"},
    {"effect": "unknown"},
    {"attempt": 0},
])
def test_invalid_case_states_fail_with_fixed_error(change: dict[str, object]) -> None:
    with pytest.raises(ReportingError, match="Run reporting failed"):
        replace(outcome("a"), **change)


def test_not_run_has_no_started_time_attempt_or_duration() -> None:
    case = CaseOutcome("queued", "LOGIN", "NOT_RUN", None, NOW, None,
                       attempt=0, duration_unavailable_reason="not_started")
    summary = summarize(RunReport(manifest(), (case,)))
    assert summary["counts"]["NOT_RUN"] == 1
    assert summary["duration_available"] == 0


def test_running_manifest_cannot_claim_finalized_success() -> None:
    with pytest.raises(ReportingError):
        replace(manifest(), reporting_complete=True)
    with pytest.raises(ReportingError):
        replace(manifest(), status="COMPLETED")


def test_unknown_run_status_fails_before_finalization() -> None:
    with pytest.raises(ReportingError):
        replace(manifest(), status="UNKNOWN", finished_at=NOW)
    with pytest.raises(ReportingError):
        check_completion(manifest(), (), "UNKNOWN")


def test_persisted_timestamps_must_use_utc() -> None:
    local = NOW.astimezone(timezone(timedelta(hours=7)))
    with pytest.raises(ReportingError):
        replace(outcome("a"), started_at=local)
    with pytest.raises(ReportingError):
        replace(manifest(), started_at=local)
