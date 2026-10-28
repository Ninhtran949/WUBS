# MASTER TASK — Build Web Stress Lab

## ROLE

You are a Staff Software Engineer, Python Architect, Automation QA Engineer, Performance Engineer, and Research Software Engineer.

Your mission is to autonomously design, bootstrap, implement, test, and maintain a research-grade Python project called:

**Web Stress Lab — Automated UI Reliability & Performance Testing Framework**

Work in the current workspace. Inspect its contents before making changes.

The project must be a genuinely executable framework, not merely a proof-of-concept script or a set of documentation files.

Primary development environment: Windows 11 with Codex CLI.

Target stack: Python 3.12+, Asyncio, Playwright, pytest, and Locust.

Use Clean Architecture, reusable engineering harnesses, modular scenario plugins, automated tests, structured observability, and reproducible research methodology.

## 1. AUTONOMOUS EXECUTION CONTRACT

Work through the complete lifecycle:

RESEARCH → SPECIFY → ARCHITECT → PLAN → IMPLEMENT → TEST → REVIEW → DOCUMENT.

Do not stop after producing a plan.

Proceed through locally testable implementation phases without asking unnecessary questions.

When an ordinary implementation decision is missing, choose the simplest secure and maintainable default, record that decision, and continue.

If a capability depends on external authorization, paid infrastructure, or a genuine human approval gate, do not bypass that requirement. Continue implementing independent local functionality.

Never invent successful test outcomes, benchmark results, or installed capabilities.

Do not push, deploy, modify unrelated repositories, or commit secrets.

Keep the working tree and existing user changes intact.

## 2. RESEARCH REQUIREMENTS

Inspect current official documentation and relevant implementation patterns from:

- https://github.com/microsoft/playwright-python
- https://github.com/microsoft/playwright-pytest
- https://github.com/pytest-dev/pytest-xdist
- https://github.com/locustio/locust
- https://github.com/ArtilleryIO/artillery
- https://github.com/grafana/k6
- https://github.com/sitespeedio/browsertime
- https://github.com/addyosmani/agent-skills

Create `docs/RESEARCH.md`.

For each relevant project, record:

1. Architecture or implementation pattern.
2. Relevant source file or documentation URL.
3. Benefits and limitations.
4. Applicability to our Python framework.
5. Decision: adopt, adapt, or reject.

Do not copy entire repositories into this project.

Use research findings to justify architecture decisions.

Prefer well-supported upstream libraries rather than writing unnecessary replacements.

## 3. INSTALL AND CONFIGURE ENGINEERING HARNESS

Use:

https://github.com/addyosmani/agent-skills

Read the repository's actual `docs/codex-setup.md` before installing.

Inspect installed Codex CLI version and available plugin commands.

If compatible, use its documented native plugin installation:

```powershell
codex plugin marketplace add addyosmani/agent-skills
codex plugin add agent-skills@agent-skills
```

If plugin setup is unsupported, use a documented compatible alternative.

Verify installation rather than assuming success.

Record the installed plugin version or source revision.

Use relevant skills contextually:

- spec-driven-development
- planning-and-task-breakdown
- constraint-driven-development
- incremental-implementation
- test-driven-development
- security-and-hardening
- performance-optimization
- observability-and-instrumentation
- code-review-and-quality
- ci-cd-and-automation

Do not load all skills simultaneously.

Do not copy the upstream repository's root AGENTS.md into this project.

Do not embed complete skill contents in the project AGENTS.md.

Create a concise, project-specific harness with progressive disclosure.

Required artifacts:

- `AGENTS.md`
- `CONSTRAINTS.md`
- `docs/SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/EXPERIMENT-METHODOLOGY.md`
- `docs/SECURITY.md`
- `docs/adr/`
- `tasks/plan.md`
- `tasks/todo.md`

Avoid redundant instructions and circular agent workflows.

## 4. PROJECT SCOPE AND SAFETY

The framework is intended for:

- Controlled web application UI testing.
- Authorized QA automation.
- Owned staging environments.
- Synthetic user workflows.
- Browser reliability experiments.
- Performance benchmarking.
- Non-destructive testing of explicitly authorized external applications.

Build a self-hosted local test application as the default target.

Support writable scenarios such as TEST_FOLLOW and TEST_COMMENT only against the local lab or explicitly authorized owned staging applications with synthetic data.

Do not automate mass social engagement on third-party platforms.

Do not introduce CAPTCHA bypass, anti-bot evasion, fingerprint camouflage, stealth proxy rotation, or mechanisms designed to avoid platform enforcement.

Unexpected authentication challenges must be classified and reported.

External stress testing must be disabled unless the experiment explicitly declares its authorized scope and resource limits.

Implement emergency stopping conditions.

## 5. CLEAN ARCHITECTURE

Use an installable `src/` layout.

Organize the system around four layers:

### Domain

Contains pure Python models, policies, contracts, results, and domain exceptions.

Must not import Playwright, Locust, Typer, FastAPI, or database implementations.

### Application

Contains experiment orchestration, bounded worker scheduling, scenario execution, account leasing, error classification, and result aggregation.

Depends on domain contracts and abstract ports.

### Infrastructure

Contains Playwright adapters, Locust subprocess integration, proxy diagnostics, secret providers, storage, metrics, and tracing.

Implement infrastructure details behind domain/application interfaces.

### Interfaces

Contains CLI, configuration entry points, and report presentation.

Avoid business logic inside CLI commands.

Use typed Python protocols or abstract interfaces where they simplify dependency boundaries.

Avoid unnecessary interfaces for trivial single-use helpers.

Follow dependency inversion and avoid circular imports.

Create architectural tests that enforce important dependency constraints.

## 6. RECOMMENDED REPOSITORY STRUCTURE

```text
web-stress-lab/
├── AGENTS.md
├── CONSTRAINTS.md
├── pyproject.toml
├── README.md
├── .env.example
├── .gitignore
├── src/
│   └── web_stress_lab/
│       ├── domain/
│       │   ├── accounts.py
│       │   ├── experiments.py
│       │   ├── scenarios.py
│       │   ├── results.py
│       │   ├── policies.py
│       │   └── errors.py
│       ├── application/
│       │   ├── orchestrator.py
│       │   ├── worker_pool.py
│       │   ├── account_lease.py
│       │   ├── scenario_service.py
│       │   └── result_service.py
│       ├── infrastructure/
│       │   ├── browser/
│       │   │   ├── playwright_engine.py
│       │   │   ├── context_factory.py
│       │   │   ├── auth_provider.py
│       │   │   └── page_objects/
│       │   ├── network/
│       │   │   └── proxy_profiles.py
│       │   ├── load/
│       │   │   └── locust_adapter.py
│       │   ├── telemetry/
│       │   │   └── collector.py
│       │   ├── storage/
│       │   │   └── repository.py
│       │   └── secrets/
│       │       └── environment_provider.py
│       ├── scenarios/
│       │   ├── base.py
│       │   ├── registry.py
│       │   ├── login.py
│       │   ├── navigation.py
│       │   ├── forms.py
│       │   └── local_social.py
│       └── cli.py
├── lab_app/
├── experiments/
├── fixtures/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── fault_injection/
├── reports/
├── docs/
├── tasks/
└── .github/
    └── workflows/
        └── ci.yml
```

Adjust the exact tree only when there is a clear architectural justification.

## 7. DATA ENGINE

Support loading test-account metadata from `test_accounts.json`.

An account may contain:

- account_id
- username
- password_ref
- totp_secret_ref
- network_profile
- browser_profile

Support importing the original test-account schema if required, but keep real credentials out of version control and persistent plaintext reports.

Implement:

- Pydantic validation.
- Duplicate-account detection.
- Missing-field detection.
- Configurable account filtering.
- Account leasing.
- Per-account execution status.
- Safe secret resolution.
- Sanitized diagnostic logs.

Use synthetic accounts for the local test application.

Implement optional `pyotp` TOTP generation for test identities controlled by the project.

Do not log OTP codes or secret seeds.

Test expired TOTP windows and expected clock-skew behavior.

Implement explicit state transitions:

AVAILABLE → LEASED → RUNNING → COMPLETED / FAILED / BLOCKED.

An account performing a state-changing scenario must not be leased by two concurrent workers.

## 8. BROWSER AUTOMATION ENGINE

Use Playwright's asynchronous Python API.

Default configuration:

- browser: Chromium
- headless: true
- browser contexts: isolated
- concurrency: 2
- configurable maximum: 10, subject to measured hardware capacity
- navigation timeout: configurable
- action timeout: configurable
- screenshots/traces: on failure by default

Implement:

- BrowserManager
- ContextFactory
- AuthProvider
- ScenarioRunner
- ContextLifecycleManager
- BrowserMetricsCollector

Reuse browser processes where practical.

Do not reuse authenticated contexts across different identities.

Allow configured browser/device profiles.

Support explicitly configured test network profiles and per-context proxy settings where permitted.

Reject unavailable or invalid network configurations with structured errors.

Do not rotate proxies to avoid rate limits or detection.

Use Playwright's locator APIs and automatic waiting.

Do not rely on positional XPath or fragile CSS selectors when stable labels and roles are available.

Support:

- login_flow()
- navigation_flow()
- form_flow()
- execute_scenario()

Use a typed scenario registry rather than a generic function that clicks arbitrary elements across unknown websites.

For owned lab targets, add TEST_FOLLOW and TEST_COMMENT flows with deterministic fixtures, state assertions, idempotency safeguards, and cleanup.

Implement authentication state via Playwright `storage_state()`.

Make persisted session reuse optional, with expiration, isolation, protected storage, and cleanup.

Test expired-session recovery.

## 9. CONCURRENCY CONTROLLER

Implement Asyncio-based orchestration:

- asyncio.Queue
- bounded worker pool
- asyncio.Semaphore
- per-origin concurrency limits
- resource-based admission control
- cancellation propagation
- backpressure
- graceful shutdown
- bounded retry logic

Do not equate Asyncio tasks with OS threads.

Keep browser contexts owned by their worker.

Never share mutable Page objects between unrelated workers.

Ensure every task reaches a terminal status and every queue item receives correct completion accounting.

The controller must support:

1. A deterministic queue execution mode.
2. A fixed-concurrency mode.
3. A gradual ramp-up mode.
4. A controlled soak mode.

Handle shutdown without leaving browser processes running.

Prevent runaway retries and duplicate state-changing operations.

## 10. THINK-TIME AND EXPERIMENT TIMING

Implement configurable timing profiles:

- no-delay
- fixed-delay
- seeded-random-delay
- ramp-up
- steady-state

Support random think time, including 3–7 seconds when specified by an experiment.

Randomness must be reproducible using an explicit seed.

Record the effective delays and seed.

Do not use arbitrary sleep as a replacement for Playwright's readiness checks.

Do not implement human-behavior simulation for evading platform automation detection.

## 11. LOCAL TEST APPLICATION

Build a small, self-contained web application under `lab_app/`.

Prefer FastAPI and simple HTML/JavaScript.

It must expose:

- Test login page.
- Synthetic users.
- Optional TOTP authentication.
- Navigation page.
- Form submission page.
- Synthetic profile/feed pages.
- Follow/unfollow test action.
- Comment creation test action.
- Authorized fixture reset.
- Configurable latency injection.
- Configurable HTTP error injection.
- Session expiry test behavior.

Use test-only data.

This application must let the complete framework operate locally without requiring accounts on external websites.

Tests must assert both browser-visible behavior and corresponding backend state.

## 12. HTTP LOAD ENGINE

Integrate Locust as a separate managed subprocess.

Do not directly mix Locust's gevent scheduling with the Playwright Asyncio event loop.

Support:

- virtual user count
- spawn rate
- test duration
- request rate policy
- workload stages
- timeout limits
- error thresholds
- managed shutdown
- statistics collection

Default all HTTP load experiments to the local lab application.

Add a comparative experimental methodology explaining:

- Browser contexts are not equivalent to virtual HTTP users.
- RPS is not the same as browser concurrency.
- Generator CPU saturation can distort observed performance.
- Open-loop and closed-loop workload models behave differently.

For Windows development, avoid assuming Unix fork-based Locust multiprocess options work.

Provide Linux/Docker instructions for advanced distributed load experiments.

## 13. FAULT HANDLING

Create explicit exception categories:

- ConfigurationError
- AccountValidationError
- AuthenticationError
- TOTPError
- ProxyConnectionError
- NavigationTimeoutError
- LocatorTimeoutError
- BrowserCrashError
- ScenarioAssertionError
- ResourceLimitError
- ScopeViolationError
- ReportingError

Do not silently discard failures.

One failed account should not terminate unrelated test cases.

A failed browser operation must still release the account lease and close resources.

Differentiate retryable and non-retryable failures.

Implement exponential backoff for eligible transient failures.

Classify blocked verification challenges separately.

Stop the entire experiment when authorization or resource safety constraints are violated.

## 14. TELEMETRY AND SCIENTIFIC MEASUREMENTS

Collect:

- experiment ID
- scenario ID
- worker ID
- anonymized account ID
- browser version
- OS information
- experiment configuration
- hardware information
- random seed
- scenario latency
- navigation timing
- action latency
- request latency
- throughput
- error rate
- timeout rate
- browser CPU/RAM where available
- generator CPU/RAM
- browser context count
- queue waiting time
- active workers
- cancellation count

Report p50, p90, p95, and p99 where there are sufficient samples.

Do not calculate misleading percentile conclusions from very small datasets.

Clearly separate browser-side timings from server-side measurements.

Support cold-start and warm-session experiments.

Record trace files and screenshots for failed scenarios.

Protect sensitive artifacts and define retention settings.

Write structured events into `system_test.log`.

## 15. REPORTING AND REPRODUCIBILITY

Each experiment must have a unique ID.

Generate:

```text
reports/<experiment_id>/
├── manifest.json
├── summary.json
├── measurements.csv
├── failures.json
├── report.html
└── artifacts/
```

The manifest must record:

- experiment parameters
- software version
- browser version
- hardware metadata
- workload settings
- seed
- start and finish timestamps
- target environment
- any deviations from the planned experiment

Implement a comparison command for compatible experiment runs.

Store raw data independently from aggregated conclusions.

Avoid fabricated metrics or unsupported causality claims.

## 16. CLI

Implement a usable CLI with commands equivalent to:

```powershell
stresslab doctor
stresslab validate-config
stresslab list-scenarios
stresslab lab start
stresslab run experiments/baseline.yaml
stresslab run experiments/ui_concurrency.yaml
stresslab report <experiment_id>
stresslab compare <run_a> <run_b>
```

Support clear terminal messages, useful error codes, and structured output.

`doctor` must verify:

- Python/runtime compatibility
- required dependencies
- browser installation
- configuration validity
- report-directory permissions
- local lab readiness

## 17. TESTING AND QUALITY GATES

Implement unit, integration, E2E, and fault-injection tests.

Minimum tests:

- account schema validation
- missing/invalid test identities
- synthetic TOTP generation
- account lease exclusivity
- browser context isolation
- per-context settings
- authentication lifecycle
- storage-state reuse
- expired-session handling
- queue worker limits
- queue cancellation
- browser crash cleanup
- missing locator timeout
- network failure handling
- retry exhaustion
- idempotent state-changing actions
- allowed-origin enforcement
- local follow/comment fixtures
- Locust process lifecycle
- report schema correctness
- secret redaction
- reproducibility metadata

Use local or mocked targets.

Never run a destructive or high-volume external experiment from CI.

Run:

```powershell
ruff check .
ruff format --check .
mypy src/
pytest -q
```

Use coverage reporting and prioritize meaningful tests of concurrency, cancellation, security boundaries, and state transitions.

Do not mark a feature complete until it passes its acceptance criteria.

Do not weaken CI, delete failing tests, or add blanket error suppression merely to produce a green result.

## 18. AUTOMATED IMPLEMENTATION PHASES

Create and maintain a complete dependency-ordered task plan.

Implement in this order:

P0 — Research, engineering harness, project constraints.

P1 — Specifications, architecture, ADRs, experiment methodology.

P2 — Installable Python project, CLI, configuration, domain models.

P3 — Local test web app and synthetic test accounts.

P4 — Playwright browser engine and end-to-end login/navigation.

P5 — Async worker pool, queue, account leasing and context management.

P6 — Scenario registry, timing profiles and lab interaction scenarios.

P7 — Locust integration and resource measurements.

P8 — Reports, comparison tools, fault-injection suite and CI.

P9 — Architecture review, security review and reproducible research release.

For every phase:

1. Identify dependent requirements.
2. Create focused tests.
3. Implement one working vertical slice.
4. Run the appropriate checks.
5. Review the diff for correctness, security and complexity.
6. Update task status and supporting documents.
7. Continue to the next independent task.

Do not implement large unverified changes.

Do not leave empty stubs labeled as completed functionality.

## 19. AGENT WORKFLOW AND MEMORY DISCIPLINE

Keep `AGENTS.md` concise and project-specific.

Use `CONSTRAINTS.md` as a persistent quality contract.

Use ADRs for architectural decisions.

Use `tasks/todo.md` as the execution checkpoint across Codex sessions.

Use progressive disclosure when reading skills and documentation.

Avoid copying the same rules into multiple files.

Avoid recursive agent-review loops that repeatedly generate documentation without implementing or verifying code.

Every major review must lead to one of:

- a confirmed defect with a fix,
- a documented accepted risk,
- or a verified passing result.

Never run expensive repeated reviews without a clearly identified change or risk.

## 20. FINAL DEFINITION OF DONE

The project foundation is complete when:

- Python package installs successfully.
- CLI runs.
- Harness setup is verified or a documented supported fallback is in place.
- Architecture and plan documents exist.
- Local lab starts.
- A synthetic test account can log in successfully.
- Optional local TOTP works.
- Two isolated browser contexts run without leaking authentication state.
- Queue concurrency is enforced.
- Browser cleanup works after timeout/cancellation.
- A local read/write scenario executes with assertions.
- A bounded Locust workload runs against the local API.
- Metrics and reports are generated from actual executions.
- Automated tests, lint, and type checks have been executed.
- Remaining work is accurately recorded in the task plan.

At completion, summarize the actual implementation state, commands executed, tests passed/failed, remaining risks, and next tasks.

Do not claim production readiness when only a local MVP has been validated.

**START NOW: Inspect the workspace, verify the required tools, install the appropriate harness, write the architecture and plan, then autonomously build and verify the complete local MVP. Continue across implementation phases as long as the work remains authorized, locally testable, and technically feasible.**
