"""Introduce external seams with their first concrete adapter."""

from typing import Protocol

from web_stress_lab.domain.experiment import Experiment
from web_stress_lab.domain.results import CaseOutcome, RunManifest, RunReport, RunStatus


class SecretProvider(Protocol):
    def resolve(self, reference: str) -> str:
        """Resolve one explicit reference; never persist or log its value."""
        ...


class ResultSink(Protocol):
    def start(self, experiment: Experiment, run_id: str, *, planned_cases: int) -> RunManifest: ...

    def record(self, outcome: CaseOutcome) -> None: ...

    def finish(self, status: RunStatus) -> RunReport: ...
