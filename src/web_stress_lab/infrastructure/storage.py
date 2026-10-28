"""One-writer local result storage and bounded read-only report loading."""

import json
import os
import platform
import re
import stat
import tempfile
from dataclasses import asdict, replace
from datetime import UTC, datetime
from html import escape
from importlib.metadata import version
from pathlib import Path, PureWindowsPath

from pydantic import ValidationError

from web_stress_lab.application.ports import ResultSink
from web_stress_lab.domain.errors import ConfigurationError, InputIssue, ReportingError
from web_stress_lab.domain.experiment import BrowserWorkload, Experiment
from web_stress_lab.domain.policy import check_scope
from web_stress_lab.domain.results import CaseOutcome, RunManifest, RunReport, RunStatus, check_cases, check_completion, summarize
from web_stress_lab.infrastructure.record_schemas import (
    RUN_ID_PATTERN, CaseRecord, ManifestRecord, case_from_json, manifest_from_json, read_json,
)

MAX_REPORT_BYTES = 1048576
_DEVICES = {"CON", "PRN", "AUX", "NUL"} | {f"{prefix}{i}" for prefix in ("COM", "LPT") for i in range(1, 10)}


def _failure(code: str) -> ReportingError:
    return ReportingError([InputIssue("$", code)])


def _guard(path: Path) -> os.stat_result | None:
    info = None
    for candidate in (*reversed(path.parents), path):
        try:
            info = candidate.lstat()
        except FileNotFoundError:
            return None
        except (OSError, ValueError):
            raise _failure("unsafe_or_unreadable_path") from None
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise _failure("reparse_path_disabled")
    return info


def _directory(root: Path, run_id: str) -> Path:
    if (not isinstance(run_id, str) or not re.fullmatch(RUN_ID_PATTERN, run_id)
        or run_id.upper() in _DEVICES):
        raise _failure("unsafe_run_id")
    raw = str(root)
    windows = PureWindowsPath(raw)
    if (raw.startswith(("\\\\", "//")) or "://" in raw or "\x00" in raw
        or (windows.drive and (os.name != "nt" or not windows.is_absolute()))):
        raise _failure("local_report_root_required")
    absolute = Path(os.path.abspath(root))
    if any(":" in part for part in absolute.parts[1:]):
        raise _failure("unsafe_report_root")
    _guard(absolute)
    path = absolute / run_id
    _guard(path)
    return path


def _regular(path: Path) -> os.stat_result:
    info = _guard(path)
    if info is None or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise _failure("regular_report_file_required")
    return info


def _read(path: Path) -> bytes:
    _regular(path)
    try:
        with path.open("rb") as source:
            data = source.read(MAX_REPORT_BYTES + 1)
    except OSError:
        raise _failure("read_failed") from None
    if len(data) > MAX_REPORT_BYTES:
        raise _failure("report_size_limit")
    return data


def _raw(directory: Path) -> RunReport:
    manifest = manifest_from_json(_read(directory / "manifest.json"))
    if manifest.run_id != directory.name:
        raise _failure("run_id_mismatch")
    raw = _read(directory / "cases.jsonl")
    if raw and not raw.endswith(b"\n"):
        raise _failure("incomplete_case_record")
    lines = raw.splitlines()
    if len(lines) > manifest.planned_cases:
        raise _failure("excess_cases")
    cases = tuple(case_from_json(line, manifest.run_id) for line in lines)
    check_cases(manifest, cases)
    if manifest.status == "COMPLETED":
        check_completion(manifest, cases, manifest.status)
    return RunReport(manifest, cases)


def render_html(report: RunReport) -> str:
    run, summary = report.manifest, summarize(report)
    rows = "".join(
        "<tr>" + "".join(f"<td>{escape(str(value))}</td>" for value in (
            item.case_id, item.scenario_id, item.status, item.attempt,
            item.duration_s if item.duration_s is not None else f"unavailable ({item.duration_unavailable_reason})",
            item.error_category or "", item.effect,
        )) + "</tr>" for item in report.cases
    )
    return (
        '<!doctype html><html lang="en"><meta charset="utf-8">'
        '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'">'
        f"<title>Run {escape(run.run_id)}</title><h1>Run {escape(run.run_id)}</h1>"
        "<p>Synthetic fixture data; not a benchmark.</p>"
        f"<p>Status: {escape(run.status)}; reporting complete: {run.reporting_complete}. "
        f"Recorded {summary['recorded_cases']} / {run.planned_cases}; "
        f"unrecorded: {summary['unrecorded_cases']}.</p>"
        f"<p>Engine: {escape(run.engine)}; origin: {escape(run.origin)}; seed: {run.seed}.</p>"
        f"<p>Python {escape(run.python_version)}; package {escape(run.package_version)}; "
        f"OS {escape(run.os_name)}.</p>"
        "<table><caption>Recorded terminal outcomes; duration in seconds</caption>"
        "<thead><tr><th>Case</th><th>Scenario</th><th>Status</th><th>Attempt</th>"
        "<th>Duration (s)</th><th>Error category</th><th>Effect</th></tr></thead>"
        f"<tbody>{rows}</tbody></table></html>"
    )


def read_run(root: Path, run_id: str) -> RunReport:
    report = _raw(_directory(root, run_id))
    if report.manifest.reporting_complete:
        directory = _directory(root, run_id)
        if read_json(_read(directory / "summary.json")) != summarize(report):
            raise _failure("summary_mismatch")
        if _read(directory / "report.html") != render_html(report).encode("utf-8"):
            raise _failure("html_mismatch")
    return report


def _publish(directory: Path, name: str, data: bytes, *, replace_existing: bool = False) -> None:
    _guard(directory)
    target = directory / name
    if replace_existing:
        _regular(target)
    fd, temporary = tempfile.mkstemp(prefix=f".{name}.", suffix=".tmp", dir=directory)
    pending = Path(temporary)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        _guard(directory)
        if replace_existing:
            _regular(target)
            os.replace(pending, target)
        else:
            # Hard-link publication is atomic and refuses an existing destination.
            os.link(pending, target)
    finally:
        pending.unlink(missing_ok=True)


def _manifest_bytes(manifest: RunManifest) -> bytes:
    return ManifestRecord.model_validate(manifest, from_attributes=True).model_dump_json().encode("utf-8")


class FileResultSink(ResultSink):
    def __init__(self, root: Path) -> None:
        self.root = root
        self._path: Path | None = None
        self._identity: tuple[int, int] | None = None
        self._initial: RunManifest | None = None

    def start(self, experiment: Experiment, run_id: str, *, planned_cases: int) -> RunManifest:
        if self._path is not None:
            raise _failure("already_started")
        path = _directory(self.root, run_id)
        try:
            origin, _ = check_scope("local_lab", experiment.engine, experiment.origin,
                                    experiment.allowed_origins, experiment.scenarios, experiment.allowed_scenarios)
            cap = experiment.workload.max_cases if isinstance(experiment.workload, BrowserWorkload) else experiment.workload.max_requests
            if planned_cases > cap:
                raise _failure("plan_exceeds_limit")
            manifest = RunManifest(run_id, experiment.engine, origin, experiment.seed, planned_cases,
                                   datetime.now(UTC), platform.python_version(), version("web-stress-lab"), platform.system())
            encoded = _manifest_bytes(manifest)
        except (ConfigurationError, ValidationError):
            raise _failure("invalid_run_metadata") from None
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            _guard(path.parent)
            path.mkdir()
            info = path.lstat()
            self._path, self._identity = path, (info.st_dev, info.st_ino)
            with (path / "cases.jsonl").open("xb") as output:
                output.flush()
                os.fsync(output.fileno())
            _publish(path, "manifest.json", encoded)
        except OSError:
            raise _failure("output_creation_failed") from None
        self._initial = manifest
        return manifest

    def _active(self) -> tuple[Path, RunReport]:
        if self._path is None:
            raise _failure("not_started")
        info = _guard(self._path)
        if info is None or (info.st_dev, info.st_ino) != self._identity:
            raise _failure("run_ownership_changed")
        report = _raw(self._path)
        if report.manifest != self._initial or report.manifest.status != "RUNNING":
            raise _failure("run_not_active")
        return self._path, report

    def record(self, outcome: CaseOutcome) -> None:
        path, report = self._active()
        try:
            record = CaseRecord.model_validate({"run_id": report.manifest.run_id, **asdict(outcome)})
        except ValidationError:
            raise _failure("invalid_case_record") from None
        check_cases(report.manifest, (*report.cases, record.outcome()))
        try:
            _regular(path / "cases.jsonl")
            with (path / "cases.jsonl").open("ab") as output:
                output.write(record.model_dump_json().encode("utf-8") + b"\n")
                output.flush()
                os.fsync(output.fileno())
        except OSError:
            raise _failure("raw_write_failed") from None

    def finish(self, status: RunStatus) -> RunReport:
        path, report = self._active()
        check_completion(report.manifest, report.cases, status)
        final = replace(report.manifest, status=status, finished_at=datetime.now(UTC), reporting_complete=True)
        result = RunReport(final, report.cases)
        try:
            check_cases(final, report.cases)
            _publish(path, "summary.json", json.dumps(summarize(result), allow_nan=False).encode("utf-8"))
            _publish(path, "report.html", render_html(result).encode("utf-8"))
            _publish(path, "manifest.json", _manifest_bytes(final), replace_existing=True)
        except (OSError, ValueError, ReportingError):
            failed = replace(final, status="FAILED", reporting_complete=False, reporting_error="finalization_failed")
            try:
                _publish(path, "manifest.json", _manifest_bytes(failed), replace_existing=True)
            except (OSError, ReportingError):
                raise _failure("finalization_and_manifest_write_failed") from None
            raise _failure("finalization_failed") from None
        return result
