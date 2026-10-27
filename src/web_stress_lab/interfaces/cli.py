"""Expose only implemented capabilities through the installed CLI."""

import argparse
from importlib.metadata import version


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="stresslab",
        description="Bounded reliability experiments against a local synthetic lab.",
    )
    parser.add_argument(
        "--version", action="version", version=f"stresslab {version('web-stress-lab')}"
    )
    parser.parse_args(argv)
    parser.print_help()
    return 0
