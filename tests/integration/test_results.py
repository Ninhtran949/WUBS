"""Synthetic outcomes round-trip through owned files, including partial failures."""

import errno
import json
import os
import subprocess
import traceback
import socket
from dataclasses import replace
from pathlib import Path

import pytest

from web_stress_lab.domain.errors import ReportingError
from web_stress_lab.domain.results import CaseOutcome, RunReport, summarize
from web_stress_lab.infrastructure.storage import FileResultSink, read_run, render_html
from web_stress_lab.interfaces.configuration import load_experiment

pytestmark = pytest.mark.integration
FIXTURE = Path(__file__).resolve().parents[2] / "fixtures/experiments/local-browser.yaml"


def started(tmp_path: Path, run_id: str = "synthetic-run", planned: int = 1):
    sink = FileResultSink(tmp_path / "reports")
    manifest = sink.start(load_experiment(FIXTURE), run_id, planned_cases=planned)
    return sink, manifest


def case(manifest, case_id: str = "case-1") -> CaseOutcome:
    return CaseOutcome(case_id, "LOGIN", "COMPLETED", manifest.started_at,
                       manifest.started_at, 0.25)


def test_synthetic_round_trip_and_final_files(tmp_path: Path) -> None:
    sink, manifest = started(tmp_path)
    first = read_run(tmp_path / "reports", manifest.run_id)
    assert first.manifest.status == "RUNNING"
    assert first.manifest.reporting_complete is False
    outcome = case(manifest)
    sink.record(outcome)
    finished = sink.finish("COMPLETED")
    report = read_run(tmp_path / "reports", manifest.run_id)
    assert report == finished
    assert report.cases == (outcome,)
    assert report.manifest.status == "COMPLETED"
    assert report.manifest.reporting_complete is True
    run = tmp_path / "reports" / manifest.run_id
    assert {x.name for x in run.iterdir()} == {
        "manifest.json", "cases.jsonl", "summary.json", "report.html"
    }
    assert json.loads((run / "summary.json").read_text()) == summarize(report)
    assert "synthetic" in (run / "report.html").read_text()
    assert "not a benchmark" in (run / "report.html").read_text()


def test_unfinalized_manifest_is_readable_without_repair_or_empty_success(tmp_path: Path) -> None:
    sink, manifest = started(tmp_path, planned=2)
    sink.record(case(manifest))
    run = tmp_path / "reports" / manifest.run_id
    before = {x.name: x.read_bytes() for x in run.iterdir()}
    report = read_run(tmp_path / "reports", manifest.run_id)
    assert summarize(report)["unrecorded_cases"] == 1
    assert report.manifest.status == "RUNNING"
    assert report.manifest.reporting_complete is False
    assert {x.name: x.read_bytes() for x in run.iterdir()} == before
    interrupted = sink.finish("INTERRUPTED")
    assert interrupted.manifest.status == "INTERRUPTED"
    assert summarize(interrupted)["unrecorded_cases"] == 1


def test_existing_run_and_raw_records_are_never_overwritten(tmp_path: Path) -> None:
    sink, manifest = started(tmp_path)
    sink.record(case(manifest))
    before = (tmp_path / "reports" / manifest.run_id / "cases.jsonl").read_bytes()
    with pytest.raises(ReportingError):
        FileResultSink(tmp_path / "reports").start(load_experiment(FIXTURE), manifest.run_id, planned_cases=1)
    with pytest.raises(ReportingError):
        sink.record(case(manifest))
    assert (tmp_path / "reports" / manifest.run_id / "cases.jsonl").read_bytes() == before
    sink.finish("COMPLETED")
    with pytest.raises(ReportingError):
        sink.record(case(manifest, "later"))
    with pytest.raises(ReportingError):
        sink.finish("COMPLETED")


def test_incomplete_success_is_rejected_before_derived_writes(tmp_path: Path) -> None:
    sink, manifest = started(tmp_path, planned=2)
    sink.record(case(manifest))
    with pytest.raises(ReportingError):
        sink.finish("COMPLETED")
    assert not (tmp_path / "reports" / manifest.run_id / "summary.json").exists()


def test_summary_disk_error_preserves_raw_outcome_and_failed_partial_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sink, manifest = started(tmp_path)
    sink.record(case(manifest))
    run = tmp_path / "reports" / manifest.run_id
    raw = (run / "cases.jsonl").read_bytes()
    original_link = os.link

    def disk_full(src, dst, *args, **kwargs):
        if Path(dst).name == "summary.json":
            raise OSError(errno.ENOSPC, "SECRET_CANARY")
        return original_link(src, dst, *args, **kwargs)

    monkeypatch.setattr(os, "link", disk_full)
    with pytest.raises(ReportingError) as caught:
        sink.finish("COMPLETED")
    assert "SECRET_CANARY" not in "".join(traceback.format_exception(caught.value))
    assert (run / "cases.jsonl").read_bytes() == raw
    report = read_run(tmp_path / "reports", manifest.run_id)
    assert report.cases == (case(manifest),)
    assert report.manifest.status == "FAILED"
    assert report.manifest.reporting_complete is False
    assert report.manifest.reporting_error == "finalization_failed"


def test_failed_manifest_update_keeps_initial_manifest_and_raw_records(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sink, manifest = started(tmp_path)
    sink.record(case(manifest))
    run = tmp_path / "reports" / manifest.run_id
    initial = (run / "manifest.json").read_bytes()
    original_replace = os.replace

    def fail_manifest(src, dst, *args, **kwargs):
        if Path(dst).name == "manifest.json":
            raise PermissionError("SECRET_CANARY")
        return original_replace(src, dst, *args, **kwargs)

    monkeypatch.setattr(os, "replace", fail_manifest)
    with pytest.raises(ReportingError):
        sink.finish("COMPLETED")
    assert (run / "manifest.json").read_bytes() == initial
    report = read_run(tmp_path / "reports", manifest.run_id)
    assert report.manifest.reporting_complete is False
    assert report.cases == (case(manifest),)


@pytest.mark.parametrize("run_id", ["../escape", "a/b", r"a\b", "CON", "NUL", "a:stream", ".", "a.", ""])
def test_unsafe_run_ids_fail_without_creating_output(tmp_path: Path, run_id: str) -> None:
    root = tmp_path / "reports"
    with pytest.raises(ReportingError):
        FileResultSink(root).start(load_experiment(FIXTURE), run_id, planned_cases=1)
    with pytest.raises(ReportingError):
        read_run(root, run_id)
    assert not root.exists()


def test_native_junction_or_symlink_root_is_rejected(tmp_path: Path) -> None:
    target, linked = tmp_path / "real", tmp_path / "linked"
    target.mkdir()
    if os.name == "nt":
        subprocess.run(["cmd", "/c", "mklink", "/J", str(linked), str(target)],
                       check=True, capture_output=True)
    else:
        linked.symlink_to(target, target_is_directory=True)
    with pytest.raises(ReportingError):
        FileResultSink(linked).start(load_experiment(FIXTURE), "safe", planned_cases=1)
    assert list(target.iterdir()) == []


@pytest.mark.parametrize("corruption", ["unknown-field", "truncated-case", "wrong-run", "oversized"])
def test_corrupt_records_fail_explicitly_and_remain_untouched(tmp_path: Path, corruption: str) -> None:
    sink, manifest = started(tmp_path)
    sink.record(case(manifest))
    run = tmp_path / "reports" / manifest.run_id
    if corruption == "truncated-case":
        path = run / "cases.jsonl"
        path.write_bytes(path.read_bytes() + b'{"SECRET_CANARY":')
    else:
        path = run / "manifest.json"
        data = json.loads(path.read_text())
        if corruption == "unknown-field":
            data["password"] = "SECRET_CANARY"
        elif corruption == "wrong-run":
            data["run_id"] = "other"
        if corruption == "oversized":
            path.write_bytes(b" " * 1048577)
        else:
            path.write_text(json.dumps(data))
    raw = path.read_bytes()
    with pytest.raises(ReportingError) as caught:
        read_run(tmp_path / "reports", manifest.run_id)
    assert path.read_bytes() == raw
    assert "SECRET_CANARY" not in "".join(traceback.format_exception(caught.value))


def test_html_escapes_untrusted_metadata(tmp_path: Path) -> None:
    _, manifest = started(tmp_path)
    payload = '<script>alert("x")</script>'
    report = RunReport(replace(manifest, python_version=payload), ())
    html = render_html(report)
    assert payload not in html
    assert "&lt;script&gt;" in html
    assert "default-src 'none'" in html


def test_raw_write_error_is_sanitized_and_keeps_initial_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sink, manifest = started(tmp_path)
    original_open = Path.open

    def denied(self, mode="r", *args, **kwargs):
        if self.name == "cases.jsonl" and mode == "ab":
            raise PermissionError("SECRET_CANARY")
        return original_open(self, mode, *args, **kwargs)

    with monkeypatch.context() as guarded:
        guarded.setattr(Path, "open", denied)
        with pytest.raises(ReportingError) as caught:
            sink.record(case(manifest))
    assert "SECRET_CANARY" not in "".join(traceback.format_exception(caught.value))
    report = read_run(tmp_path / "reports", manifest.run_id)
    assert report.cases == ()
    assert report.manifest.reporting_complete is False


def test_record_validation_and_plan_limit_happen_before_append(tmp_path: Path) -> None:
    sink, manifest = started(tmp_path)
    with pytest.raises(ReportingError):
        sink.record(replace(case(manifest), account_ref="RAW_USERNAME_CANARY"))
    assert read_run(tmp_path / "reports", manifest.run_id).cases == ()
    sink.record(case(manifest))
    with pytest.raises(ReportingError):
        sink.record(case(manifest, "excess"))
    assert read_run(tmp_path / "reports", manifest.run_id).cases == (case(manifest),)


def test_initial_manifest_failure_does_not_fabricate_empty_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original_link = os.link

    def denied(src, dst, *args, **kwargs):
        if Path(dst).name == "manifest.json":
            raise PermissionError("SECRET_CANARY")
        return original_link(src, dst, *args, **kwargs)

    monkeypatch.setattr(os, "link", denied)
    with pytest.raises(ReportingError):
        started(tmp_path)
    with pytest.raises(ReportingError):
        read_run(tmp_path / "reports", "synthetic-run")


def test_replaced_owned_directory_is_not_written(tmp_path: Path) -> None:
    sink, manifest = started(tmp_path)
    root = tmp_path / "reports"
    run, preserved = root / manifest.run_id, root / "preserved"
    assert run.resolve().parent == preserved.resolve().parent == root.resolve()
    run.rename(preserved)
    run.mkdir()
    for source in preserved.iterdir():
        (run / source.name).write_bytes(source.read_bytes())
    before = {p.name: p.read_bytes() for p in run.iterdir()}
    with pytest.raises(ReportingError):
        sink.record(case(manifest))
    assert {p.name: p.read_bytes() for p in run.iterdir()} == before


@pytest.mark.parametrize("artifact", ["summary.json", "report.html"])
def test_final_read_checks_derived_output_against_raw_records(tmp_path: Path, artifact: str) -> None:
    sink, manifest = started(tmp_path)
    sink.record(case(manifest))
    sink.finish("COMPLETED")
    run = tmp_path / "reports" / manifest.run_id
    raw = (run / "cases.jsonl").read_bytes()
    (run / artifact).write_text("{}" if artifact.endswith(".json") else "SECRET_CANARY")
    with pytest.raises(ReportingError):
        read_run(tmp_path / "reports", manifest.run_id)
    assert (run / "cases.jsonl").read_bytes() == raw


def test_read_report_never_resolves_secrets_or_starts_execution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from web_stress_lab.infrastructure.secrets import EnvironmentSecretProvider

    _, manifest = started(tmp_path)

    def deny(*args, **kwargs):
        raise AssertionError("Unexpected execution")

    monkeypatch.setattr(EnvironmentSecretProvider, "resolve", deny)
    monkeypatch.setattr(subprocess, "Popen", deny)
    monkeypatch.setattr(socket, "socket", deny)
    assert read_run(tmp_path / "reports", manifest.run_id).manifest == manifest
