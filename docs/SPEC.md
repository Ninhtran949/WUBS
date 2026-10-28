# Web Stress Lab specification

Status: SE/SA design baseline, 2026-10-27; [PROJECT](PROJECT.md) records implementation progress and available commands. Source: [Task.md](../Task.md). This specification makes that brief implementable and adapts its recommended harness/tree to the existing repository. It is not an execution authorization or an implementation report.

## Objective and scope

Deliver an installable Python framework for reproducible UI reliability experiments and bounded HTTP load against a bundled synthetic lab. Windows 11 is the primary development platform; Linux portability is tested. Target stack: Python 3.12+, Asyncio, Playwright, pytest, Locust. Engineering choices and boundaries are recorded in [ARCHITECTURE](ARCHITECTURE.md) and its ADRs.

The local foundation includes real CLI, lab, browser and HTTP execution, account ownership, timing, error handling, measurements, reports, and automated verification. Optional TOTP, protected session reuse, and explicitly supported network profiles are separate capabilities with visible availability checks. External execution remains disabled until the authorization and enforcement gates in [SECURITY](SECURITY.md) pass.

Non-goals for this foundation: third-party engagement automation, evasion, distributed controllers, cloud orchestration, a metrics service, a web dashboard, generic arbitrary-site clicking, or downloading/executing plugins from experiment files.

## Capability map and acceptance

Each row is an independently testable capability. Implement only the assigned slice from the [plan](plans/implementation-plan.md); its task IDs identify dependencies and checks.

| ID | Capability / owner | Observable acceptance | Task.md source |
| --- | --- | --- | --- |
| F01 | Configuration and scope / interfaces + domain | Safe YAML/JSON loading and Pydantic validation reject unknown fields, duplicate/unknown IDs, nonfinite values and unsafe bounds. Scope rejection happens before secret resolution, browser launch or network work. | 4, 7, 9, 16 |
| F02 | Identities and secrets / domain + adapters | JSON account metadata validates unique IDs, profiles, and secret references. Filters are deterministic. Missing secrets fail without exposing values. Optional TOTP tests cover expiry and configured clock skew. | 7 |
| F03 | Synthetic lab / packaged lab app | Login, optional TOTP, navigation, forms, profiles/feed, follow/unfollow, comments, namespace-scoped reset, latency/error injection, and session expiry work locally. Tests assert UI and backend state. | 11 |
| F04 | Browser engine / infrastructure | Async Chromium, isolated contexts, explicit per-context profiles, login and optional storage-state reuse operate with tested expiry recovery. Failure/stop/crash closes owned resources without cross-identity state leakage. | 8, 13 |
| F05 | Run controller / application | Bounded queues, workers, origin admission, exclusive leases, backpressure and stop propagation work. Every accepted case has terminal accounting. One case failure is isolated; policy/resource violations stop the experiment. | 7, 9 |
| F06 | Trusted scenarios / browser adapters | Typed registry supports login, navigation, forms, TEST_FOLLOW and TEST_COMMENT. Payload validation, backend assertions, stable operation IDs, reconciliation and namespace cleanup prevent duplicate writes. | 8, 11 |
| F07 | Workload and timing / domain + application | Deterministic queue, fixed concurrency, bounded ramp and soak modes are distinct from no/fixed/seeded-random think time. Per-case random draws and effective delays are recorded independently of completion order. | 9, 10 |
| F08 | HTTP load / managed Locust adapter | A separate process enforces user/spawn/stage settings, finite duration, request budgets, global request-rate safety cap, timeouts, error thresholds and owned shutdown. Stats are ingested without mixing schedulers. | 12 |
| F09 | Measurements / adapters + application | Record provenance and the requested latency, throughput, error/timeout, resource, context, queue, worker and cancellation metrics with units and availability. Browser/request/server timings remain distinct. | 14 |
| F10 | Durable results / storage + presentation | Unique run directories contain raw data, manifest, summaries, failures and safe HTML. Interrupted/partial runs and reporting failures remain visible; prior runs are never overwritten. | 14, 15 |
| F11 | CLI and comparison / interfaces | All commands below give useful exit codes and optional JSON. Comparison validates engine, target/workload, sample and environment compatibility before drawing conclusions. | 15, 16 |
| F12 | Engineering qualification / tests + CI | Import boundaries, unit/integration/E2E/fault tests, quality gates, installed-wheel smoke, and bounded local CI pass with recorded evidence. No external load in CI. | 5, 17, 20 |

F01 and F03 enable browser work; F02/F04 enable F05/F06; F05 enables F07. F08 shares only validated policy/results with the browser engine. F09/F10 grow with each executing slice instead of waiting until the last phase. F12 starts at bootstrap and gates each capability.

## Input contract

An experiment has `schema_version`, a seed, one `engine` (`browser` or `http`), target/scope, typed scenario selections, account catalog/filter, workload, think-time settings, finite limits, artifact policy, and output location. A single run never silently combines engines. Paths are config-relative; secret values are never valid report/config fields.

Target scope records normalized exact origins (scheme, host, port), permitted scenario capabilities, resource limits, and an authorization reference/expiry when external. Wildcards, credentials in URLs, unsupported schemes, arbitrary imports/commands, and attempts to override a registered scenario's mutability are rejected. Read [SECURITY](SECURITY.md) for enforcement rather than treating this record as permission.

Account metadata supports `account_id`, `username`, `password_ref`, optional `totp_secret_ref`, `network_profile` and `browser_profile`. References initially use explicitly named environment variables; legacy account formats require an explicit adapter and fixture, not guessed field mappings. Runtime credentials stay outside serializable domain results.

### T02 static configuration contract

Version 1 accepts a UTF-8 JSON/YAML object (at most 64 KiB, 32 nesting levels and 4,096 nodes). Duplicate mapping keys, aliases, nonstandard YAML tags, unknown fields, coercion of strings/bools into numbers and nonfinite numbers are rejected. Error output contains fixed categories/codes and schema field locations, never source excerpts or rejected values.

Required fields are `schema_version: 1`, `engine`, `target.origin`, `scope.allowed_origins`, `scope.allowed_scenarios` and `scenarios` (objects with an `id` only). Browser inputs also require `accounts.catalog`; optional `accounts.include_ids` is a unique list of account IDs. Catalog contents and secrets are not loaded by T02. Seed defaults to 0 (0 through 2^63-1). Identifiers are bounded, duplicate selections are rejected, and scenario engine/capabilities cannot be overridden.

The initial closed scenario metadata recognizes `LOGIN` for `browser` and `HTTP_HEALTH` for `http`. These are **static contracts, not available execution handlers**. T06/T09/T14 attach actual engines/handlers; later scenarios extend the trusted metadata when implemented. Unknown IDs, arbitrary module names, scenario parameters and unsupported profiles/session persistence fail validation.

The supported target mode is `local_lab`. Exact origins use HTTP/HTTPS, literal `127.0.0.1` or `[::1]`, an explicit port 1-65535 and no credentials, query, fragment or non-root path. Normalization removes a trailing `/` and canonicalizes the scheme/port. The local scope must contain exactly the target origin and must permit the selected scenarios. External/owned-staging declarations remain blocked; validation never establishes target ownership or runtime readiness.

Paths use portable relative components under the configuration directory, without `..`, drive/UNC/device/ADS syntax, shell metacharacters or reserved Windows names. The catalog ends in `.json`; `output_dir` defaults to `reports`. Paths are resolved against the config directory independently of CWD; existing symlink/junction/reparse components are rejected before following them. Only the configuration file is read. Missing catalog/output paths are allowed because catalog validation and durable output belong to T03/T04. Runtime adapters must recheck containment at use time.

| Field | Default / static bounds |
| --- | --- |
| Browser `workload` | `mode: queue`, concurrency 2 (1-10 requested), per-origin concurrency 2 (1-10), queue size 10 (1-100), max cases 10 (1-10), navigation/action timeouts 15/5 s (0-15 s, positive), max attempts 2 (1-2). Requested concurrency is not resource admission. |
| HTTP `workload` | `mode: constant`, users 2 (1-2), spawn rate 1 user/s (0-1, positive), max requests 100 (1-100), max RPS 5 (0-5, positive, burst 1), request timeout 5 s (0-15, positive). Higher loads/stages require later capacity/enforcement capabilities. |
| `limits` | Max duration 60 s for browser / 30 s for HTTP (0-60, positive); shutdown timeout 30 s (0-30, positive), covering the longest operation plus a 5 s cleanup reserve. An operation or think-time bound cannot exceed run duration. |
| `think_time` | `mode: none`; alternatively `fixed` with `delay_s` or `seeded_random` with `min_s`/`max_s` (defaults 3/7). Delays are finite 0-60 s and min <= max; T11 implements scheduling. |
| `artifacts` | `capture: on_failure` (`on_failure`/`never`), retention 7 days (1-30). Capture/retention execution is a later capability. |

`validate-config <file> --json` returns `ok`, `validation: static` and `execution_checked: false`; success summarizes the engine, normalized origin and scenario IDs. Failures return an error category and sanitized field/code issues. Exit 2 identifies malformed/unsupported configuration and exit 3 identifies blocked target/scope. Human output uses the same sanitized information. Validation creates no output, resolves no secrets and starts no process, browser, DNS lookup or HTTP request.

### T03 identity catalog and secret references

The catalog is a bounded UTF-8 JSON object with `schema_version: 1` and `accounts`
(1-100 entries). It uses the same 64 KiB / depth / node / duplicate-key / local
regular-file guards as experiment inputs. YAML catalogs, legacy arrays or legacy
field names, unknown fields and inline credential values are rejected explicitly;
no implicit migration or field guessing is supported.

Each account requires `account_id`, `username` and `password_ref`. IDs follow the
experiment identifier contract. Usernames are 1-128 Unicode characters without
ASCII controls or surrounding whitespace. IDs and exact usernames must be unique
throughout the catalog, including entries excluded by a filter. No case folding is
inferred. Optional `totp_secret_ref` is metadata only; TOTP execution belongs to T12.
Profile references initially accept only `network_profile: direct` and
`browser_profile: default` (also the defaults); T08 adds executable profiles.

Secret references have the exact form `env:NAME`, where NAME is 1-128 portable
environment-name characters (`[A-Za-z_][A-Za-z0-9_]*`). The provider reads only the
explicitly named variable, without enumeration, interpolation, file loading or
fallback names. Invalid references and absent/empty values raise sanitized
`AccountValidationError` issues with exit 2; values and variable names are excluded
from diagnostics. Resolved values stay outside account/domain result objects.

`load_accounts(path, include_ids=...)` validates the entire catalog before
filtering. Its Python API takes an ID tuple (the experiment parser converts its
JSON/YAML ID list); an empty tuple selects all entries and duplicate/unknown IDs fail.
Selection preserves catalog order independently of requested-ID order and does
not read secrets, create outputs, start processes or access the network.
T02's `validate-config` continues to read only the experiment file. Runtime
scope/admission/lease ordering before secret resolution is tested in T06/T07.

### T04 initial durable results and read-only reports

T04 adds the first storage slice: an exclusive `reports/<run_id>/` directory,
version-1 `manifest.json` and append-only `cases.jsonl`, followed by atomically
published `summary.json` and escaped `report.html`. CSV, extracted failures,
structured engine events and richer measurements arrive with their later tasks;
the foundation report contract below remains required. T04 data is explicitly
`data_source: synthetic`; it does not claim engine observations or benchmarks.

A manifest records run ID, engine/origin/seed, planned case count (1-100), UTC
start/end, Python/package/OS provenance, run status and `reporting_complete`.
Initial RUNNING manifests are incomplete. Successful finalization publishes the
derived reports before the final manifest. A summary/HTML write failure preserves
raw outcomes, attempts a FAILED/incomplete manifest with a fixed reporting code,
and raises `ReportingError`. If that update also fails, the initial incomplete
manifest remains evidence; it never implies success.

Terminal case outcomes record case/scenario IDs, attempt (1-2, or 0 before starting), optional opaque
account reference (`acct_` plus 32 lowercase hex characters), UTC timestamps,
terminal status, duration in seconds or an explicit unavailability reason, fixed
error category and confirmed/unknown effect. No username, credential/reference,
raw exception message or arbitrary payload field is persisted. Duplicate case IDs
and outcomes beyond the plan fail; retry-attempt telemetry is a later extension.
COMPLETED finalization requires every planned case to be recorded as COMPLETED
with confirmed effects. Other terminal/partial statuses preserve missing counts.

The writer uses one owned run directory, bounded records, flushed raw appends and
atomic derived writes. Existing run IDs are never reused; traversal, links/reparse
components, malformed records, collisions and I/O failures produce sanitized
`ReportingError` issues (exit 4). This is one-writer local storage; runtime lock,
recovery/admission and account-pseudonym creation are T06/T07 integration gates.

`report <run_id> [--root reports] [--json]` reads and validates existing records
without creating files, resolving secrets or starting engines/network work. It
shows persisted status, synthetic source, completeness and counts, including
unrecorded cases. A RUNNING/incomplete manifest is shown as unfinalized; the reader
does not guess whether a process is alive or silently mark it INTERRUPTED.

### Initial defaults

These are configuration defaults, not measured hardware capacity. Only the Chromium/headless/isolation/concurrency values come directly from Task.md; remaining values are conservative SE/SA baseline choices to test and refine explicitly.

| Setting | Initial contract |
| --- | --- |
| Target | Bundled loopback lab; exact port is declared by the experiment/launcher. |
| Browser | Chromium, headless, fresh isolated context per case; no persistent auth by default. |
| Browser concurrency | 2; absolute requested ceiling 10, further limited by origin and measured resource admission. No automatic rise to 10. |
| Navigation / action timeout | 15 s / 5 s. |
| Shutdown budget | 30 s, including a bounded cleanup reserve; validate compatibility with operation deadlines. |
| Baseline work | At most 10 cases and 60 s; every mode has a finite maximum even for soak. |
| Retry | One eligible retry after the initial attempt; seeded bounded exponential backoff, all attempts recorded. Never automatic for an unknown write outcome. |
| Think time | No delay by default; fixed or seeded random (including configured 3-7 s) is explicit. |
| HTTP smoke | 2 users, spawn 1 user/s, duration 30 s, at most 100 requests and 5 requests/s with burst 1. This is a safety cap, not an achievable-throughput claim. |
| Artifacts | On failure for the synthetic local lab; other environments require an explicit permitted artifact policy. |
| Retention | Local protected artifacts expire after 7 days by default; reports record policy, and cleanup is limited to verified owned artifact paths. |

Higher loads require explicit configuration, a capacity calibration record, and safety gates. Missing metrics are unavailable with a reason, never zero or assumed headroom.

## Lifecycle and failure contracts

- Account execution follows `AVAILABLE -> LEASED -> RUNNING -> COMPLETED / FAILED / BLOCKED`; accepted queued/running cases additionally support terminal `CANCELLED` and `NOT_RUN` accounting on stop. An ordinary case failure does not fail sibling tasks by exception propagation.
- Account availability/lease ownership is separate from immutable case history. Releasing a lease does not erase a completed result or immediately unblock a challenged identity. Each lease has an owner token; release occurs only after the adapter can no longer act.
- Run statuses distinguish `RUNNING`, `COMPLETED`, `FAILED`, `BLOCKED`, `CANCELLED` and recovered `INTERRUPTED`. An incomplete manifest or missing final summary never implies success.
- Case results include identifiers, scenario, attempt, terminal status, categorized failure, timestamps/durations, measurement availability, and effect certainty (`confirmed` or `unknown`). Cancellation after submission can leave an unknown mutation; preserve it for reconciliation.
- Error categories include `ConfigurationError`, `AccountValidationError`, `AuthenticationError`, `TOTPError`, `ProxyConnectionError`, `NavigationTimeoutError`, `LocatorTimeoutError`, `BrowserCrashError`, `ScenarioAssertionError`, `ResourceLimitError`, `ScopeViolationError`, and `ReportingError`. Unexpected verification challenges are BLOCKED, not a login retry loop. Sanitized causes preserve diagnostic meaning.

## CLI contract

Target commands (availability is recorded in PROJECT; help/version and static validate-config are implemented):

```text
stresslab doctor
stresslab validate-config <experiment.yaml>
stresslab list-scenarios
stresslab lab start
stresslab run <experiment.yaml>
stresslab report <experiment_id>
stresslab compare <run_a> <run_b>
```

Support machine-readable JSON and concise human output. `validate-config` is static validation, without launching engines or resolving secrets. `doctor` reports runtime/dependency/browser availability, validated config, output access, and local lab readiness; it does not install tools or probe external targets silently. List/report/compare commands do not run scenarios.

Exit codes: 0 success, 1 observed scenario/threshold failure, 2 invalid input/usage, 3 blocked authorization/admission, 4 infrastructure/reporting failure, 130 user cancellation. Include the primary cause and any cleanup/reporting failure in structured output rather than losing them behind one numeric code.

## Report contract and foundation completion

Each `reports/<experiment_id>/` contains `manifest.json`, `summary.json`, `measurements.csv`, `failures.json`, `report.html`, `system_test.log` (sanitized structured events), and an `artifacts/` directory when artifacts exist. Schemas are versioned; raw records carry run/case/scenario/attempt IDs, units and sampling context. The manifest records resolved sanitized configuration, tool/browser/OS/hardware versions, seed, workload, start/end, target, calibration, retention, and deviations.

Use the sample/percentile/comparison policy in [EXPERIMENT-METHODOLOGY](EXPERIMENT-METHODOLOGY.md). Small smokes prove function, not performance.

The product foundation is complete only with an installed-wheel CLI, real local lab login and optional TOTP capability result, two isolated authenticated contexts, enforced queue/lease limits, timeout/cancellation/crash cleanup, an asserted local write scenario, a bounded Locust run, genuine reports, and executed lint/type/full applicable tests. Record any unavailable optional feature explicitly. Documentation completion alone does not meet this product gate.
