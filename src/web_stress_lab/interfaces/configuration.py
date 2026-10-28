"""Strict boundary schemas converted once into standard-library domain values."""

from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError

from web_stress_lab.domain.errors import ConfigurationError, InputIssue
from web_stress_lab.domain.experiment import (
    AccountSelection,
    ArtifactPolicy,
    BrowserWorkload,
    Experiment,
    HttpWorkload,
    RunLimits,
    ThinkTime,
)
from web_stress_lab.domain.policy import check_scope, check_timing
from web_stress_lab.interfaces.configuration_files import read_document, reference_path

type Identifier = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")]
type OperationSeconds = Annotated[float, Field(gt=0, le=15)]
type DelaySeconds = Annotated[float, Field(ge=0, le=60)]


class InputModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        allow_inf_nan=False,
        frozen=True,
        validate_default=True,
    )


class TargetInput(InputModel):
    mode: Literal["local_lab", "owned_staging", "external_read_only"] = "local_lab"
    origin: Annotated[str, Field(min_length=1, max_length=2048)]


class ScopeInput(InputModel):
    allowed_origins: Annotated[list[str], Field(min_length=1, max_length=4)]
    allowed_scenarios: Annotated[list[Identifier], Field(min_length=1, max_length=16)]


class ScenarioInput(InputModel):
    id: Annotated[str, Field(pattern=r"^[A-Z][A-Z0-9_]{0,63}$")]


class AccountsInput(InputModel):
    catalog: Annotated[str, Field(min_length=1, max_length=240)]
    include_ids: Annotated[list[Identifier], Field(max_length=100)] = Field(
        default_factory=list
    )


class BrowserWorkloadInput(InputModel):
    mode: Literal["queue"] = "queue"
    concurrency: Annotated[int, Field(ge=1, le=10)] = 2
    per_origin_concurrency: Annotated[int, Field(ge=1, le=10)] = 2
    queue_size: Annotated[int, Field(ge=1, le=100)] = 10
    max_cases: Annotated[int, Field(ge=1, le=10)] = 10
    navigation_timeout_s: OperationSeconds = 15
    action_timeout_s: OperationSeconds = 5
    max_attempts: Annotated[int, Field(ge=1, le=2)] = 2


class HttpWorkloadInput(InputModel):
    mode: Literal["constant"] = "constant"
    users: Annotated[int, Field(ge=1, le=2)] = 2
    spawn_rate: Annotated[float, Field(gt=0, le=1)] = 1
    max_requests: Annotated[int, Field(ge=1, le=100)] = 100
    max_rps: Annotated[float, Field(gt=0, le=5)] = 5
    burst: Annotated[int, Field(ge=1, le=1)] = 1
    request_timeout_s: OperationSeconds = 5


class LimitsInput(InputModel):
    max_duration_s: Annotated[float, Field(gt=0, le=60)] = 60
    shutdown_timeout_s: Annotated[float, Field(gt=0, le=30)] = 30


class NoDelayInput(InputModel):
    mode: Literal["none"] = "none"


class FixedDelayInput(InputModel):
    mode: Literal["fixed"]
    delay_s: DelaySeconds


class RandomDelayInput(InputModel):
    mode: Literal["seeded_random"]
    min_s: DelaySeconds = 3
    max_s: DelaySeconds = 7


type DelayInput = Annotated[
    NoDelayInput | FixedDelayInput | RandomDelayInput, Field(discriminator="mode")
]


class ArtifactsInput(InputModel):
    capture: Literal["on_failure", "never"] = "on_failure"
    retention_days: Annotated[int, Field(ge=1, le=30)] = 7


class CommonInput(InputModel):
    schema_version: Annotated[int, Field(ge=1, le=1)]
    seed: Annotated[int, Field(ge=0, le=2**63 - 1)] = 0
    target: TargetInput
    scope: ScopeInput
    scenarios: Annotated[list[ScenarioInput], Field(min_length=1, max_length=10)]
    think_time: DelayInput = Field(default_factory=NoDelayInput)
    artifacts: ArtifactsInput = Field(default_factory=ArtifactsInput)
    output_dir: Annotated[str, Field(min_length=1, max_length=240)] = "reports"


class BrowserInput(CommonInput):
    engine: Literal["browser"]
    accounts: AccountsInput
    workload: BrowserWorkloadInput = Field(default_factory=BrowserWorkloadInput)
    limits: LimitsInput = Field(default_factory=LimitsInput)


class HttpInput(CommonInput):
    engine: Literal["http"]
    accounts: None = None
    workload: HttpWorkloadInput = Field(default_factory=HttpWorkloadInput)
    limits: LimitsInput = Field(default_factory=lambda: LimitsInput(max_duration_s=30))


_ADAPTER = TypeAdapter(
    Annotated[BrowserInput | HttpInput, Field(discriminator="engine")]
)
_FIELDS = {"browser", "http"} | {
    name
    for model in (
        TargetInput,
        ScopeInput,
        ScenarioInput,
        AccountsInput,
        BrowserWorkloadInput,
        HttpWorkloadInput,
        LimitsInput,
        NoDelayInput,
        FixedDelayInput,
        RandomDelayInput,
        ArtifactsInput,
        BrowserInput,
        HttpInput,
    )
    for name in model.model_fields
}


def load_experiment(path: Path) -> Experiment:
    document, base = read_document(path)
    try:
        parsed = _ADAPTER.validate_python(document)
    except ValidationError as error:
        issues = []
        for detail in error.errors(
            include_input=False, include_context=False, include_url=False
        ):
            location = (
                ".".join(
                    str(part) if isinstance(part, int) or part in _FIELDS else "?"
                    for part in detail["loc"]
                )
                or "$"
            )
            issues.append(InputIssue(location, detail["type"]))
        raise ConfigurationError(issues) from None
    scenarios = tuple(item.id for item in parsed.scenarios)
    origin, allowed_origins = check_scope(
        parsed.target.mode,
        parsed.engine,
        parsed.target.origin,
        parsed.scope.allowed_origins,
        scenarios,
        parsed.scope.allowed_scenarios,
    )
    delay = parsed.think_time
    minimum = (
        delay.delay_s
        if isinstance(delay, FixedDelayInput)
        else (delay.min_s if isinstance(delay, RandomDelayInput) else 0.0)
    )
    maximum = (
        delay.delay_s
        if isinstance(delay, FixedDelayInput)
        else (delay.max_s if isinstance(delay, RandomDelayInput) else 0.0)
    )
    accounts = None
    workload: BrowserWorkload | HttpWorkload
    if isinstance(parsed, BrowserInput):
        browser = parsed.workload
        operation = max(browser.navigation_timeout_s, browser.action_timeout_s)
        workload = BrowserWorkload(
            browser.mode,
            browser.concurrency,
            browser.per_origin_concurrency,
            browser.queue_size,
            browser.max_cases,
            browser.navigation_timeout_s,
            browser.action_timeout_s,
            browser.max_attempts,
        )
        ids = parsed.accounts.include_ids
        if len(ids) != len(set(ids)):
            raise ConfigurationError(
                [InputIssue("accounts.include_ids", "duplicate_value")]
            )
        accounts = AccountSelection(
            reference_path(base, parsed.accounts.catalog, "accounts.catalog"),
            tuple(ids),
        )
    else:
        http = parsed.workload
        operation = http.request_timeout_s
        workload = HttpWorkload(
            http.mode,
            http.users,
            http.spawn_rate,
            http.max_requests,
            http.max_rps,
            http.burst,
            http.request_timeout_s,
        )
    check_timing(
        parsed.limits.max_duration_s,
        parsed.limits.shutdown_timeout_s,
        operation,
        minimum,
        maximum,
    )
    return Experiment(
        parsed.schema_version,
        parsed.seed,
        parsed.engine,
        origin,
        allowed_origins,
        tuple(parsed.scope.allowed_scenarios),
        scenarios,
        accounts,
        workload,
        RunLimits(parsed.limits.max_duration_s, parsed.limits.shutdown_timeout_s),
        ThinkTime(delay.mode, minimum, maximum),
        ArtifactPolicy(parsed.artifacts.capture, parsed.artifacts.retention_days),
        reference_path(base, parsed.output_dir, "output_dir", directory=True),
    )
