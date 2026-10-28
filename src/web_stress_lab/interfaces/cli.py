"""Expose only implemented capabilities through the installed CLI."""

import argparse
import json
import sys
from importlib.metadata import version
from pathlib import Path

from web_stress_lab.domain.errors import ConfigurationError
from web_stress_lab.interfaces.configuration import load_experiment


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
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    common = {"validation": "static", "execution_checked": False}
    try:
        experiment = load_experiment(args.path)
    except ConfigurationError as error:
        issues = [{"field": issue.field, "code": issue.code} for issue in error.issues]
        if args.json:
            print(
                json.dumps(
                    {
                        **common,
                        "ok": False,
                        "error": {"category": type(error).__name__, "issues": issues},
                    }
                )
            )
        else:
            print(f"{type(error).__name__}: {error.message}", file=sys.stderr)
            for issue in error.issues:
                print(f"  {issue.field}: {issue.code}", file=sys.stderr)
        return error.exit_code
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
