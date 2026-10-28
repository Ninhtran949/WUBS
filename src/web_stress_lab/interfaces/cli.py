"""Expose only implemented capabilities through the installed CLI."""

import argparse
import json
import sys
from importlib.metadata import version
from pathlib import Path

from web_stress_lab.domain.errors import ConfigurationError, ReportingError
from web_stress_lab.domain.results import summarize
from web_stress_lab.interfaces.bootstrap import load_report
from web_stress_lab.interfaces.configuration import load_experiment


def _error(
    error: ConfigurationError | ReportingError,
    as_json: bool,
    common: dict[str, object],
) -> int:
    issues = [{"field": issue.field, "code": issue.code} for issue in error.issues]
    if as_json:
        print(json.dumps({**common, "ok": False,
                          "error": {"category": type(error).__name__, "issues": issues}}))
    else:
        print(f"{type(error).__name__}: {error.message}", file=sys.stderr)
        for issue in error.issues:
            print(f"  {issue.field}: {issue.code}", file=sys.stderr)
    return error.exit_code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="stresslab",
        description="Bounded reliability experiments against a local synthetic lab.",
    )
    parser.add_argument(
        "--version", action="version", version=f"stresslab {version('web-stress-lab')}"
    )
    commands = parser.add_subparsers(dest="command")
    validate = commands.add_parser(
        "validate-config", help="Validate a static experiment"
    )
    validate.add_argument("path", type=Path)
    validate.add_argument(
        "--json", action="store_true", help="Emit machine-readable output"
    )
    report = commands.add_parser("report", help="Read an existing run without modifying it")
    report.add_argument("run_id")
    report.add_argument("--root", type=Path, default=Path("reports"))
    report.add_argument("--json", action="store_true", help="Emit machine-readable output")
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    if args.command == "report":
        try:
            summary = summarize(load_report(args.root, args.run_id))
        except ReportingError as error:
            return _error(error, args.json, {"read_only": True})
        if args.json:
            print(json.dumps({"ok": True, "read_only": True, "report": summary}))
        else:
            print(f"Report {summary['run_id']}: {summary['status']} ({summary['data_source']}); "
                  f"reporting complete: {summary['reporting_complete']}.")
            print(f"Recorded {summary['recorded_cases']} / {summary['planned_cases']}; "
                  f"unrecorded: {summary['unrecorded_cases']}.")
        return 0
    common: dict[str, object] = {"validation": "static", "execution_checked": False}
    try:
        experiment = load_experiment(args.path)
    except ConfigurationError as error:
        return _error(error, args.json, common)
    summary = {
        "engine": experiment.engine,
        "origin": experiment.origin,
        "scenarios": list(experiment.scenarios),
    }
    if args.json:
        print(json.dumps({**common, "ok": True, "experiment": summary}))
    else:
        print(
            f"Valid static {experiment.engine} configuration: {experiment.origin}; "
            f"{', '.join(experiment.scenarios)}. Execution has not been checked."
        )
    return 0
