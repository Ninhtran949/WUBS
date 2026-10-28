"""Immutable configuration values; no schema/framework objects cross inward."""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from web_stress_lab.domain.policy import Engine


@dataclass(frozen=True)
class AccountSelection:
    catalog: Path
    include_ids: tuple[str, ...]


@dataclass(frozen=True)
class BrowserWorkload:
    mode: Literal["queue"]
    concurrency: int
    per_origin_concurrency: int
    queue_size: int
    max_cases: int
    navigation_timeout_s: float
    action_timeout_s: float
    max_attempts: int


@dataclass(frozen=True)
class HttpWorkload:
    mode: Literal["constant"]
    users: int
    spawn_rate: float
    max_requests: int
    max_rps: float
    burst: int
    request_timeout_s: float


@dataclass(frozen=True)
class RunLimits:
    max_duration_s: float
    shutdown_timeout_s: float


@dataclass(frozen=True)
class ThinkTime:
    mode: Literal["none", "fixed", "seeded_random"]
    min_s: float
    max_s: float


@dataclass(frozen=True)
class ArtifactPolicy:
    capture: Literal["never", "on_failure"]
    retention_days: int


@dataclass(frozen=True)
class Experiment:
    schema_version: int
    seed: int
    engine: Engine
    origin: str
    allowed_origins: tuple[str, ...]
    allowed_scenarios: tuple[str, ...]
    scenarios: tuple[str, ...]
    accounts: AccountSelection | None
    workload: BrowserWorkload | HttpWorkload
    limits: RunLimits
    think_time: ThinkTime
    artifacts: ArtifactPolicy
    output_dir: Path
