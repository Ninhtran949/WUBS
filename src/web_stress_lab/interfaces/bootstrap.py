"""Construct concrete adapters at the interface composition boundary."""

from pathlib import Path

from web_stress_lab.domain.results import RunReport
from web_stress_lab.infrastructure.storage import read_run


def load_report(root: Path, run_id: str) -> RunReport:
    return read_run(root, run_id)
