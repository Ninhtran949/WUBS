# Coding and development conventions

Status: target conventions for future product code. [PROJECT](PROJECT.md) distinguishes available commands from planned gates. [CONSTRAINTS](../CONSTRAINTS.md) owns non-negotiable limits; this document owns implementation practices.

## Python and dependencies

- Target Python 3.12+. Use `pyproject.toml` as the tool/configuration entry point, `uv.lock` for exact resolution, and `.venv` for the project environment. Pin the CI toolchain; record browser revisions as well as Python package versions.
- Use a minimal setuptools build backend for the `src/` package and package the local lab resources in the wheel. Test the wheel from a directory outside the source tree.
- Product dependencies have a concrete owner: Playwright in browser infrastructure; Locust in its child process; Pydantic and safe YAML parsing at config boundaries; FastAPI/Uvicorn in the optional lab; psutil in resource probes. `pyotp` is optional. Keep test, coverage, lint, and type tooling in the dev group; keep lab/load/TOTP extras explicit.
- Resolve and review dependency changes deliberately. Inspect install/build hooks before execution; prefer wheels and supported upstream packages. Do not run remote install scripts, automatic forced audit fixes, or add a library for a few trivial lines.
- Domain uses standard-library dataclasses, enums, and typed values. Convert boundary schemas into domain objects once. No ORM, DI container, generic repository framework, or mirrored Playwright locator API.

## Names, types, and errors

- Use English code identifiers and documentation; `snake_case` modules/functions, `PascalCase` classes/exceptions, and `UPPER_SNAKE_CASE` constants/enum members. Add `_s`, `_ms`, or `_bytes` when a unit could be ambiguous.
- Annotate public functions, ports, return values, and mutable collections. Use `Protocol` at the actual external seams identified in the architecture. Avoid `Any`, unchecked casts, wildcard imports, mutable defaults, and service-locator globals.
- Use Ruff's 88-character formatting baseline and targeted lint rules configured once in `pyproject.toml`; use strict mypy for `src/`. Narrow, justified suppressions require a local reason and a test; blanket exclusions do not satisfy a gate.
- Keep configuration unknown-field rejection, finite-number checks, positive bounds, duplicate IDs, unknown scenario rejection, and secret-reference syntax at the input boundary. Cross-field safety decisions remain domain/application policy.
- Use the error categories in SPEC. Map library exceptions at adapter boundaries while preserving a sanitized cause category. Do not silently fall back to success, retry every exception, expose raw exception payloads, or swallow cancellation.
- Comment the reason for an otherwise surprising choice, not its mechanics. A knowingly limited shortcut uses `shortcut: <limit>, <upgrade trigger>` and is disclosed in the task result.

## Asyncio, processes, and state

- A run owns its tasks, queues, contexts, child processes, and handles. Retain task references and await all owned work. No detached fire-and-forget tasks or unbounded `gather` over accounts.
- Match every successful queue `get()` with exactly one `task_done()` in `finally`, including sentinels. Unclaimed queued cases need explicit terminal accounting during shutdown. Use Python 3.12-compatible sentinels/stop events; do not depend on later `Queue.shutdown()` APIs.
- Catch ordinary case failures inside the worker; propagate scope/resource/reporting failures to the supervisor's stop policy. Preserve `CancelledError` after required cleanup. Stop admission before shutdown; do not cancel in-flight Playwright calls directly. The adapter must own, bound, drain, and observe shielded operations; shield is not permission to leak tasks.
- Serialize lease acquisition and release; a lease token must match its owner. Do not free a lease by an elapsed timer while its worker or context may still act. Never share mutable Page/BrowserContext objects between workers or identities.
- Use `asyncio.create_subprocess_exec` with argument lists and `sys.executable`; no shell-built commands or imported Locust code in the controller. On Windows keep the subprocess-capable event loop. Terminate only processes owned by the run; never kill all Chromium/Python processes by name.
- Represent writes with stable operation IDs. Retry only eligible read/transient operations within budget. A timeout after submitting a write requires backend-state reconciliation or an unknown outcome; it is not proof of failure.
- Use `pathlib`, explicit UTF-8, timezone-aware UTC timestamps, and monotonic clocks for elapsed time. Resolve config-relative paths against the config file, not an incidental CWD. Validate output containment and collisions before writing; never overwrite a previous run.

## Browser and lab code

- Use the async Playwright API directly inside infrastructure scenario handlers; prefer role/label/test-ID locators, auto-waiting, and observable state assertions. Think time is an experiment setting, not a readiness workaround.
- Keep the trusted scenario registry in Python code with typed payloads and immutable capability metadata. User YAML selects an ID; it cannot import a module, execute code, change whether a scenario mutates state, or turn off scope checks.
- Test browser-visible outcomes and authoritative lab state. Lab handlers keep synthetic state/idempotency checks atomic and run in one process; tests must reset only their own fixture namespace.
- Browser settings are passed explicitly to contexts created by our adapter; pytest plugin flags do not automatically configure API-created contexts. Auth-state persistence and network profiles are explicit, tested capabilities.

## Tests and quality gates

| Test location (planned) | Responsibility |
| --- | --- |
| `tests/unit/` | Pure rules, config, classifications, timing, aggregation. No network/browser. |
| `tests/architecture/` | AST-based absolute/relative import boundaries; forbid controller imports of Locust/gevent and inner imports of outer packages. |
| `tests/integration/` | Real file sinks, process locks, lab state, subprocess lifecycle, isolated browser adapters. |
| `tests/e2e/` | Installed CLI and complete local synthetic workflows. |
| `tests/fault_injection/` | Cancellation, ambiguous writes, resource limits, browser crashes, denied scope, disk failures, and cleanup. |
| `tests/test_harness.py` | Existing upstream-integrity/layout tests; preserve them. |

- Write the meaningful regression/behavior test first for new logic; see it fail for the expected reason. Use a fake only at an external seam; include a real-adapter test for lifecycle guarantees that a fake cannot prove.
- Register `unit`, `architecture`, `integration`, `e2e`, `fault_injection`, and `load` markers with strict marker checking. Default full product CI runs required local tests; no credentials or external targets. Expensive soak/load runs are separately bounded and explicitly selected.
- Async application tests use explicit pytest-asyncio loop scopes. Adopt the upstream async Playwright fixtures only where appropriate; do not mix sync browser objects into async controller tests or change the Windows loop policy to make a fixture pass.
- Use deterministic clocks/seeds/barriers for race tests; no timing-sensitive arbitrary sleeps as assertions. Cover cleanup and unknown outcomes, not only successful output.
- Follow the commands in PROJECT. The release gate includes lint, format, mypy, the full applicable suite, coverage with critical-branch review, wheel installation, and the SPEC foundation acceptance. A selected subset is reported as that subset.
- Do not add arbitrary coverage percentages before measuring the suite. Require direct evidence for exclusivity, scope, cancellation, idempotency, and redaction; a high aggregate percentage cannot substitute for them.
- Keep test execution serial initially. Optional pytest-xdist needs isolated ports, data, report roots, and identity catalogs; it is not the product worker pool. Benchmark qualification remains serial with controlled host load.

## Agent checkpoint

Before code: state the assigned requirement/task, affected boundaries, acceptance criteria, and checks. For a substantial task, update the existing plan checkpoint instead of creating another task list.

After code: review behavior, failures, security, and complexity; record commands and observed results, files changed, unresolved risks, and the next dependency. Only mark a task complete with evidence. Do not claim a local test as hosted CI or a smoke run as a benchmark. Stop at the requested boundary.
