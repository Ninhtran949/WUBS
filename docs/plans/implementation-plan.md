# Web Stress Lab implementation plan

Status: implementation authorized by the Owner on 2026-10-27 ("read the project and develop according to the plan"). On 2026-10-28 the Owner requested baseline CI before further feature work. T01's local bootstrap/review fixes are verified on Windows; T01a prepares and qualifies hosted CI before T02. T02-T20 remain pending. This is the single task checklist/checkpoint; no commit, push, deployment or external load is authorized.

Sources: [SPEC](../SPEC.md), [CONSTRAINTS](../../CONSTRAINTS.md), [ARCHITECTURE](../ARCHITECTURE.md), [CONVENTIONS](../CONVENTIONS.md), [SECURITY](../SECURITY.md), [methodology](../EXPERIMENT-METHODOLOGY.md), [research](../RESEARCH.md). Follow the six existing skills contextually; no new pack/router is needed.

## Execution rules and checkpoints

- On an implementation request, select its authorized task(s), inspect current code/status, and verify dependencies first. If the user authorizes the complete local foundation, continue through its independent local slices; a request for one slice does not authorize every later task.
- Each task adds a working vertical behavior, tests it, reviews affected boundaries/failures, and updates this same checkpoint. A task's listed directories are responsibilities, not a mandate to create every suggested module.
- Baseline CI starts at bootstrap. Every later capability updates the existing workflow, dependency/provisioning steps and required tests in the same change; T19 qualifies the accumulated pipeline rather than introducing CI for the first time. See [ADR-0003](../adr/0003-ci-at-bootstrap.md).
- Use a meaningful failing test before new logic, then focused checks and the applicable broader gates from PROJECT. Add tests with the feature, not only at the final fault-suite task.
- Ordinary per-case failures are isolated. Authorization, resource, ownership, cleanup and reporting failures are explicit gates. Do not bypass unsupported features or missing host capabilities to mark progress.
- Record actual commands/results next to the task when executed; keep unchecked items pending. Do not commit, push, deploy, start external load or execute remote installers just because this plan lists future work.

Suggested checkpoints after T04, T08, T12, T15, and T20 verify all completed slices remain usable. An architectural change updates its ADR/spec before dependent implementation; it does not erase previous evidence.

## P2: Package, baseline CI, inputs and first durable output

- [x] **T01 - Installable package and toolchain (F11/F12).** Complete on Windows after the Owner's review fixes; see the checkpoints below. Dependencies: none; establish Python 3.12+ and reviewed uv first. Scope: `pyproject.toml`, `uv.lock`, minimal `src/web_stress_lab/` CLI/composition entry, quality config, installation/import tests, planned ignores and placeholder-only environment example.
  - Acceptance: a wheel installs and `stresslab --help`/version work outside the checkout; exact compatible Python/tool/dependency choices are recorded. No pretend browser/lab capability.
  - Acceptance: domain/application import boundary tests enforce the architecture from their first modules; existing harness tests remain intact.
  - Verify: locked environment, wheel smoke, Ruff/format/mypy and collected focused tests; use PROJECT commands after creating their configuration. Review installation/build hooks before execution.

- [ ] **T01a - Baseline CI before feature implementation (F12).** Dependencies: T01. Scope: `.github/workflows/ci.yml`, CI conventions and hosted qualification evidence. Workflow preparation and hosted success are separate gates.
  - Acceptance: push/PR/manual triggers run pinned uv/project Python, locked installation, lint/format/types, harness verification, all ordinary non-load tests, isolated build and fresh-wheel smoke on Ubuntu and Windows. Actions are SHA-pinned, repository permission is read-only, and failures are not suppressed.
  - Acceptance: an authorized published revision containing the workflow, `uv.lock`, required source documents and current code produces successful `Checks (ubuntu-24.04)` and `Checks (windows-2025)` jobs. Record the actual run URL/commit SHA and per-platform test/build artifacts before checking this task off.
  - Verify: actionlint and local workflow-command checks establish preparation only. Hosted Actions setup, Linux execution, artifact upload and runner behavior require actual GitHub evidence. Keep T01a pending until that evidence exists; publication requires separate commit/push authorization.

- [ ] **T02 - Validated experiment and scope contract (F01).** Dependencies: T01/T01a. Scope: domain policies/errors, `interfaces/configuration.py`, `validate-config`, input fixtures and tests.
  - Acceptance: valid local YAML/JSON becomes a domain experiment; malformed/unsafe inputs, unknown fields/IDs, invalid bounds and unsupported features fail with structured errors.
  - Acceptance: disallowed origins/capabilities fail before secret lookup, process creation or network access. Static validation has no execution side effects.
  - Verify: schema, cross-field limits, unsafe YAML, path, URL/port and no-outbound negative tests; CLI JSON/exit-code test and architecture checks.

- [ ] **T03 - Identity catalog and secret references (F02).** Dependencies: T02. Scope: domain account values, boundary account parser/filter, environment secret adapter, synthetic fixtures.
  - Acceptance: validate duplicates, required fields, profile references, deterministic filtering and explicit legacy-schema rejection/adaptation.
  - Acceptance: missing/malformed secret references are classified without logging values; the provider accepts explicit references only. Admission/lease ordering at its runtime call site is an integration gate in T06/T07.
  - Verify: validation/filter tests, secret-provider boundary tests, log/error redaction tests, unchanged input fixtures.

- [ ] **T04 - Initial run record and read-only report path (F10/F11).** Dependencies: T02. Scope: file result sink, minimal report presentation, versioned run/case schemas and filesystem tests.
  - Acceptance: a test-supplied synthetic outcome round-trips through real file I/O; initial/final/partial manifests differ visibly. Unique output directories never overwrite older runs. Genuine engine observations attach in T06/T14.
  - Acceptance: raw observations survive summary failure; path traversal/collision/write errors yield ReportingError rather than fabricated empty success.
  - Verify: round-trip, interrupted manifest, unsafe/junction path where supported, disk-error and HTML-escaping tests. Mark fixtures as synthetic, not benchmark runs.

## P3-P4: Local target and first real browser

- [ ] **T05 - Packaged lab login and isolated fixture namespace (F03).** Dependencies: T01/T02. Scope: `lab_app/`, packaged HTML/seeds, `lab start`, authenticated fixture controls and lab tests.
  - Acceptance: an installed CLI starts a loopback single-process lab with synthetic login/navigation, health/readiness and namespace-scoped state/reset; no source-CWD dependency.
  - Acceptance: tests assert authoritative state and reject wrong-namespace reset; stop/interrupt closes only the owned lab process.
  - Verify: real local server lifecycle plus endpoint/state tests and installed-wheel lab smoke; no external service/accounts.

- [ ] **T06 - Async browser login and stop proof (F04).** Dependencies: T03/T04/T05. Scope: browser lifecycle/auth adapter, one-case application lifecycle/lease ownership, first login scenario, real Chromium integration tests. T07 extends this owned slice into the bounded pool.
  - Acceptance: two isolated contexts authenticate synthetic identities without leaking state; actual outcomes and browser version reach the result sink.
  - Acceptance: navigation timeout, stop during a browser action and browser failure leave no owned context/driver tasks or processes after the bounded shutdown path; uncertain effects are represented honestly.
  - Verify: Windows real-browser lifecycle tests, context isolation, native timeouts, cancellation/drain and crash cleanup. This is a blocking experiment for the architecture, not a claim a fake can prove.

## P5: Ownership, concurrency and browser settings

- [ ] **T07 - Exclusive leases and bounded workers (F05).** Dependencies: T06. Scope: application run/scheduling/lease logic, local OS run-lock adapter, concurrency tests.
  - Acceptance: queue size, total/origin admission and identity exclusivity hold under contention; stale owner tokens cannot release another lease. A second controller is rejected, and an unresolved interrupted run blocks unsafe catalog/target reuse.
  - Acceptance: failure of one case is isolated; queued/in-flight cancellation accounts for every accepted case and acknowledges queue items once, holding leases through cleanup.
  - Verify: deterministic concurrency/barrier tests, two-process OS-lock and interrupted-controller recovery tests on Windows/Linux, real-browser worker cleanup and final-count reconciliation.

- [ ] **T08 - Explicit context, session and network profiles (F04/F02).** Dependencies: T06/T07. Scope: context factory/auth-state/profile adapters and tests.
  - Acceptance: browser/device/per-context settings are applied explicitly; unsupported proxy/network profiles return structured errors without insecure fallback or evasive rotation.
  - Acceptance: optional protected auth state is account/origin/profile-bound, expires, recovers through login, and is cleaned safely; default persistence remains off.
  - Verify: real context-option/identity tests, expired session recovery, storage access failure, local proxy/network failure and secret/artifact isolation.

## P6: Scenarios, timing and optional TOTP

- [ ] **T09 - Trusted registry, navigation and form scenario (F06).** Dependencies: T05/T06. Scope: browser scenario registry/handlers/page objects, lab form endpoint/UI, `list-scenarios` and tests.
  - Acceptance: typed registered IDs and payloads select login/navigation/form behavior with role/label locators and frontend/backend assertions.
  - Acceptance: config cannot import code or change an ID's engine/mutability; unknown IDs fail during static validation.
  - Verify: registry/CLI tests and real browser form/navigation paths, including missing locator and injected HTTP errors.

- [ ] **T10 - Follow/comment writes with reconciliation (F06/F03).** Dependencies: T07/T09. Scope: synthetic social handlers/UI, atomic lab idempotency/state endpoints and failure tests.
  - Acceptance: TEST_FOLLOW/TEST_COMMENT assert state for the authenticated synthetic actor; stable operation IDs prevent duplicate writes.
  - Acceptance: timeout/cancellation after commit is reconciled or remains unknown/BLOCKED, with no blind resend; cleanup/reset affects only owned fixtures.
  - Verify: concurrent writes, duplicate operation, wrong actor, unknown outcome, replay and namespace reset; external/non-owned write selection is rejected before execution.

- [ ] **T11 - Deterministic timing and bounded modes (F07).** Dependencies: T07/T09. Scope: pure scheduling/timing policy, application admission and timing records.
  - Acceptance: deterministic queue, fixed, ramp and finite soak modes run; no/fixed/seeded-random delay includes configured 3-7 s without substituting for browser readiness.
  - Acceptance: equivalent seed/planned-case inputs reproduce assignments and draws independent of worker completion order; effective delays and stop bounds are recorded.
  - Verify: fake-clock/seed policy tests, backpressure/stop boundaries and short real local runs; do not call timings themselves deterministic.

- [ ] **T12 - Optional synthetic TOTP flow (F02/F03).** Dependencies: T03/T06. Scope: optional pyotp adapter, lab challenge and auth flow.
  - Acceptance: controlled test identities authenticate with the declared TOTP policy; missing optional support is visible and does not generate fake success.
  - Acceptance: expired code, configured skew, bad seed and unexpected challenge are classified, with no codes/seeds in logs, reports or artifacts.
  - Verify: clock-controlled unit tests and local TOTP browser path plus sanitization evidence; no real account/MFA bypass.

## P7: Resource admission and managed HTTP load

- [ ] **T13 - Measurement and resource admission (F09/F05).** Dependencies: T07/T11. Scope: resource probes, timestamped observations, admission policy and doctor capability output.
  - Acceptance: record generator/owned-process CPU/RAM where available, queue/workers/context gauges and latency boundaries with units and missing reasons.
  - Acceptance: measured budgets constrain admission; missing evidence cannot raise browser concurrency above the conservative baseline. Resource violations stop and finalize the run.
  - Verify: simulated limit/missing-probe tests, real local samples, calibration manifest and bounded low-load run. No published capacity numbers without an actual calibration.

- [ ] **T14 - One managed Locust workload (F08).** Dependencies: T02/T04/T05/T13. Scope: subprocess adapter, one approved local HTTP workload, process/request-budget tests.
  - Acceptance: bounded headless single-process execution uses allowed targets, curated environment and argument lists; the controller imports no Locust/gevent.
  - Acceptance: duration, request count, per-request global cap and process stop deadlines are enforced from the first executable workload; child errors/partial stats are preserved.
  - Verify: real tiny local run and raw observations, process crash/hang/stop, failed limiter, invalid arguments and no orphan child on Windows. No fork-based `--processes` fallback.

- [ ] **T15 - HTTP stages and result ingestion (F08/F09).** Dependencies: T14. Scope: validated users/spawn/stage policy, workload request listener/statistics ingestion and tests.
  - Acceptance: user/spawn/ramp/steady settings and error thresholds work within the independent hard budgets. Task pacing is not reported as a guaranteed global RPS.
  - Acceptance: request observations/statistics retain provenance and counts; losses, truncated data and saturation are visible. Browser and HTTP records cannot be silently pooled.
  - Verify: local stages/cap/threshold tests and per-request event reconciliation. A failed ingestion fails its reporting gate rather than inventing metrics.

## P8: Reports, comparison, fault coverage and CI

- [ ] **T16 - Complete durable experiment report (F10/F09).** Dependencies: T10/T11/T13/T15. Scope: aggregate calculation, manifest/failures/CSV/HTML and artifact retention.
  - Acceptance: the report tree in SPEC is generated from actual raw records with outcome denominators, sample thresholds, units, metadata and safe HTML; interrupted/partial runs remain explicit.
  - Acceptance: auth/secrets are excluded; artifact access/retention and contained cleanup are enforced; report regeneration does not mutate raw data.
  - Verify: schema/aggregate fixtures, too-few-samples and missing metrics, HTML injection, disk failure, redaction and cleanup boundary tests; real local browser and HTTP report examples.

- [ ] **T17 - Compatible run comparison (F11).** Dependencies: T16. Scope: comparison use case and CLI/presentation.
  - Acceptance: compare only compatible engine/model/scenario/fixture/cohort/warm-state/windows; identify hardware/software/network deviations and reject automatic equivalence when needed.
  - Acceptance: repeated-run variation and insufficient samples remain visible; no UI-versus-RPS equivalence or unsupported causal/performance claim.
  - Verify: compatible/incompatible/incomplete fixture comparisons and a repeated local functional demonstration clearly labeled as smoke unless research criteria are met.

- [ ] **T18 - Adversarial lifecycle and egress gate (F01/F04/F05/F08/F12).** Dependencies: T08/T10/T14/T16. Scope: fault suite strengthening existing feature tests and conditional external-capability qualification.
  - Acceptance: local fault targets exercise redirects/subresources/service workers/popups/WebSockets, scope escapes, wrong ownership, cancellation/retry exhaustion, unknown writes and reporting failure; no forbidden traffic/effects are hidden.
  - Acceptance: unsupported strict egress or protected-state guarantees keep external mode blocked. Local tests do not authorize a real external experiment.
  - Verify: the SECURITY threat matrix against real adapters plus import-boundary tests. Record concrete failures/accepted limits once; do not open recursive review loops.

- [ ] **T19 - Full pipeline qualification and operational instructions (F12).** Dependencies: T01/T01a/T02-T18. Scope: the existing CI pipeline, complete platform/browser qualification, README and Linux/Docker advanced-load guidance.
  - Acceptance: qualify the Windows/Linux pipeline grown since T01a, including implemented unit/architecture/integration/E2E/fault coverage and installed-wheel smoke. Each capability must already have added its required setup/tests; do not defer those additions to T19. Expensive load/soak jobs stay separately bounded and explicitly selected.
  - Acceptance: documented fresh-checkout instructions distinguish optional features, environment setup, secrets, browser provisioning, retention, and unsupported/distributed cases. Missing browsers/required tests fail their gate visibly.
  - Verify: available local commands and workflow configuration; record actual hosted run/job/artifact evidence only when separately available/authorized. Workflow files and local tests alone are not a green hosted run.

## P9: Foundation review

- [ ] **T20 - Review and qualify the local foundation (F12).** Dependencies: T01-T19 implementation; report any unavailable hosted/external gate separately. Scope: one bounded architecture/security/quality review and evidence-led fixes within the authorized work.
  - Acceptance: every SPEC foundation item has real evidence: wheel/CLI, lab/TOTP availability, context isolation, queue/lease bounds, stop/crash cleanup, asserted local write, bounded Locust and genuine reports.
  - Acceptance: full applicable tests/lint/types/build and threat/measurement reviews are recorded; no skipped requirement is relabeled complete. Remaining optional, hosted, distributed and external gates are explicit.
  - Verify: run the declared qualification on actual local resources, reconcile requirement/test/status mappings, update PROJECT and this checkpoint, then report local foundation status without claiming production readiness.

## Execution evidence

Design/document checkpoint, 2026-10-27:

- `python -B scripts/verify_harness.py`: passed, including six skills, upstream hashes, metadata, layout and required reference paths.
- `python -B -m unittest discover -s tests -p test_harness.py -v`: all 12 existing harness tests passed.
- Local structural/snapshot checks passed: five existing documentation files updated, nine design documents added, 46 relative links resolved, one root instruction file, 12 capabilities covered, and 20 pending tasks with backward-only dependencies.
- `Task.md`, all 16 existing `.agents/` files, `.gitattributes`, the verifier and tests retain their baseline bytes. No product code, dependencies, global plugin configuration, Git repository, commit, push or deployment was created.
- Scope routing was reviewed for trivial edits, substantial behavior, security risk and measurement work; spec/plan/commit defaults are explicitly overridden without modifying upstream skills. Product commands are labeled planned rather than reported as executed.

These checks verify the design checkpoint only. At that checkpoint, no product tests, quality-tool runs, hosted CI or performance experiments had occurred. The implementation evidence below supersedes its initial environment inventory; task acceptance still requires every listed gate.

Initial implementation dependency: T01. Design-time preflight gaps were active Python 3.11.9 versus target 3.12+, uv/Ruff/mypy absent from PATH, no product manifest/lock/browser provisioning, and no Git metadata.

### Initial T01 checkpoint, 2026-10-27 (partial; superseded below)

- Authorization: the Owner requested autonomous development according to this plan. Work started at T01; no Git repository was initialized and no commit, push, deployment or external load was performed.
- Scope: installable `src/web_stress_lab/` with a standard-library help/version CLI, `pyproject.toml`, `.python-version`, ignores and placeholder-only `.env.example`; CLI/architecture tests; a fresh-wheel smoke check. No empty domain/application/adapter modules or placeholder browser/lab commands were created.
- Toolchain: workspace-local Python 3.12.16 and uv 0.13.6; setuptools 84.2.1; Ruff 0.17.3; mypy 2.4.0; pytest 9.1.1, pytest-asyncio 1.4.1 and pytest-cov 7.1.0. See PROJECT for official artifact URLs, verified SHA-256 digests, startup-hook review and bootstrap details. Seventeen PyPI development/backend wheels were installed offline into `.venv`; this was **not a locked install**.
- RED: the initial CLI/import tests failed as expected (four failures: missing package/CLI, nine architecture-detector checks passed). GREEN: the installed CLI and import tests then passed on Python 3.12.16. Negative architecture fixtures cover absolute/relative, TYPE_CHECKING, third-party inner-layer, lab/controller and Locust/gevent violations.
- The original harness verifier and test received import sorting/formatting only to satisfy the newly established quality configuration. No assertion or verification rule was removed or weakened. Task.md and vendored skill/reference/license/provenance bytes were not edited.
- Build evidence: `.tools/uv.exe build --python '.venv/Scripts/python.exe' --offline --no-build-isolation` built the source archive and `dist/web_stress_lab-0.1.0-py3-none-any.whl`. The backend was preinstalled from its reviewed wheel. Inspecting both archives confirmed no local toolchain, environment, reports or run data were included, despite uv's cache-location warning.
- Wheel evidence: `.venv/Scripts/python.exe scripts/smoke_wheel.py dist/web_stress_lab-0.1.0-py3-none-any.whl --uv .tools/uv.exe` passed: fresh temporary environment outside checkout, offline wheel installation, real console help/version, isolated import from `site-packages`. The smoke currently supports the dependency-free T01 wheel; T02 must provision its locked runtime dependencies when added.
- Final available checks: `.venv/Scripts/python.exe -m pytest -q --cov --cov-report=term-missing` passed all 26 tests (12 original harness tests and 14 new tests). Coverage was 100% of the current 10 product statements, not evidence for unimplemented capabilities. `.venv/Scripts/ruff.exe check .`, `.venv/Scripts/ruff.exe format --check .`, and `.venv/Scripts/mypy.exe src/` all passed; strict mypy checked four source files. `python -B scripts/verify_harness.py` passed six-skill integrity. A fresh-context report-only review found no material issue in the scoped T01 package, tests, archive contents, CLI, architecture guard or smoke; it did not repeat the final suite. Linux execution, locked installation, hosted CI, browser/load and later tasks remain unverified.
- **Blocking gate:** `uv lock --no-build --no-python-downloads` against the local Python failed to fetch `https://pypi.org/simple/pytest/` with WinError 10013. Requested sandbox escalation was rejected by the session approval policy (`sandbox_approval: false`). A subsequent `uv lock --offline --no-build` failed because registry metadata for mypy was not cached. Downloading wheel files did not satisfy that registry-resolution gate. No lockfile was hand-authored, no checks were bypassed and T01 stays unchecked.
- Ruling: stop at T01's dependency gate rather than implement T02-T20 against an unverified locked environment. Resume by generating/reviewing `uv.lock` with uv 0.13.6 and running the locked PROJECT gates where uv can reach PyPI. Preserve the current code and local evidence; no new spec, plan, router or bootstrap installer is needed.

### T01 completion checkpoint, 2026-10-27

- Scope: finish T01 as requested before T02. Product source and tests are unchanged from the reviewed initial implementation. This completion adds the generated `uv.lock`, minimal locked-install commands in README, and current status/evidence in PROJECT and this checkpoint. No T02 implementation was started.
- The previous network block is resolved: approved uv network access generated the lock with `lock --python .tools/python/python/python.exe --cache-dir .tools/cache --default-index https://pypi.org/simple --no-build --no-python-downloads`. uv resolved 17 packages (16 dev dependencies and the editable project), preserving the selected versions.
- Dependency review: all registry sources are `https://pypi.org/simple`, all distribution URLs are official `files.pythonhosted.org` URLs with SHA-256 hashes, and no Git/local override or arbitrary URL dependency was introduced. All 16 selected dev wheel hashes match the initially reviewed PyPI artifacts. The exact setuptools 84.2.1 build-system pin remains unchanged; no third-party source build was allowed.
- Clean locked install: with `UV_PROJECT_ENVIRONMENT` set to the previously absent `.tools/t01-locked-env`, `uv sync --locked --all-extras --group dev --python .tools/python/python/python.exe --cache-dir .tools/cache --no-build --no-python-downloads` created the environment and installed all 17 packages successfully. A second locked sync of the existing `.venv` passed offline; the manually installed backend was removed from that environment and build isolation was restored.
- Locked quality gates passed using `.tools/uv.exe run --locked --offline --cache-dir .tools/cache`: `ruff check .`, `ruff format --check .`, `mypy src/`, `python -m pytest -q --cov --cov-report=term-missing`, and `python -B scripts/verify_harness.py`. Results: 26 tests passed (12 harness, 14 new); strict mypy passed four source files; Ruff and formatting passed; six-skill integrity passed. Coverage is 100% of the current 10 product statements only.
- Isolated build: `.tools/uv.exe build --python .venv/Scripts/python.exe --cache-dir .tools/cache --offline --no-python-downloads` passed without disabling isolation, producing both source archive and wheel. Inspection confirmed the wheel contains only the package/distribution metadata and the source archive excludes local tools, environments, run data and Git metadata, despite uv's cache-location warning.
- Fresh installed-wheel smoke: `uv run --locked --offline python scripts/smoke_wheel.py dist/web_stress_lab-0.1.0-py3-none-any.whl --uv .tools/uv.exe` passed with the workspace cache: offline installation into a new temporary environment outside checkout, real console help/version and isolated `site-packages` import.
- `uv lock --check --offline --cache-dir .tools/cache` passed without changing the lock. Qualification lock SHA-256: `a13650271c8c0b306f1ae97ff15ebaab2fe4eb3b72c88d659c19848471ca4524`. Git metadata is now present; this task did not initialize it. No commit, push, deployment or external load was performed.
- Review: initial product/package/architecture review remains applicable; the completion delta was checked for dependency provenance, hash consistency, clean installation, build isolation, raw archive contents and inaccurate status claims. No architecture or application behavior changed, and no new ADR was needed.
- T01's package/toolchain acceptance is met on Windows. Linux qualification and hosted CI remain future T19 gates; browser/lab/load and other foundation capabilities remain pending. Next task: T02.

### T01 Owner review fixes, 2026-10-27

- The Owner identified three defects missed by the prior checks: root package files were skipped, the workload prefix admitted sibling modules, and ignored/untracked `Task.md` was absent from `git archive HEAD`. The pre-fix archive confirmed the missing source document; no previous local check established a complete Git handoff.
- RED: the new focused tests produced 14 expected failures: nine root-file scanner cases (Locust/gevent/Playwright in `__init__.py`, `__main__.py`, `helper.py`), four forbidden sibling-name cases, and one missing-source-document check. Positive namespace and valid root-import cases were also added. The initial focused run had 31 passing cases.
- Root policy: the scanner now examines every package Python file. Root modules use the standard library; `__main__.py` may dispatch to interfaces. The real entry point and valid stdlib helpers remain allowed. Domain/application rules and the explicit bootstrap boundary remain intact.
- Workload policy: Locust/gevent are allowed only in the exact `web_stress_lab.infrastructure.load.workload` module/package and dot-separated descendants. `workload_controller` and `workload_helper` are rejected. ARCHITECTURE documents these enforced boundaries; product code and dependency direction did not change.
- Source handoff: removed `Task.md` from `.gitignore`, added `/Task.md -text` with a file-specific CRLF allowance retaining Git's normal whitespace checks, and staged only `Task.md`, `.gitignore`, `.gitattributes` for this finding. The original 21,948 bytes (735 CRLF lines) and staged blob match SHA-256 `ac1f9e74d01cbd41637e56cc81fe9f87cb5a5b8c388c21ee9d7dfaf840364c98`. `git ls-files --error-unmatch Task.md`, the no-ignore check and cached Git attributes confirm the prepared handoff. `Task.md` itself was not edited. HEAD remains unchanged until a separately authorized commit.
- The harness verifier now requires `Task.md`; its fixture copies the real source document and its new negative test removes it to prove rejection. Existing assertions and all vendored skill/reference/license/provenance bytes remain intact.
- GREEN: locked full pytest/coverage passed **49 tests**: 32 architecture, 13 harness, three installed-CLI integration and one CLI unit test. Locked Ruff check/format and strict mypy passed; harness integrity passed. Coverage remains 100% of 10 product statements, not a coverage claim about the guard tests or later capabilities.
- Rebuilt source archive/wheel with the isolated pinned backend and reran fresh installed-wheel smoke outside checkout; both passed. `uv.lock` and runtime package code remain unchanged. No dependency or architecture service was introduced.
- All three requested fixes are ready for review. T02, Linux and hosted CI remain unexecuted; no commit or push was performed.

### T01a baseline CI preparation, 2026-10-28

- Authorization: the Owner requested the early CI plan/workflow correction. Added the baseline workflow and ADR-0003; T01 remains the verified local bootstrap, T01a precedes T02, and T19 now qualifies the full accumulated pipeline.
- Prepared push/PR/manual checks on `ubuntu-24.04` and `windows-2025`. Official checkout, setup-uv and upload-artifact releases were resolved to their exact commit SHAs and their action inputs checked. The workflow keeps repository permission read-only, credentials unpersisted, bounded jobs, normal failure propagation, and narrowly selected test/build artifacts.
- Native actionlint 1.7.12 passed. Its official Windows release archive was SHA-256 verified before execution. YAML/safety checks passed for triggers, matrix, action pins, permissions, no suppressed check failures and the project Python pin. PowerShell parsing passed for every run step.
- Executed the exact post-provisioning run blocks extracted from the workflow in a clean temporary copy of the working tree, initially without `.venv` or ignored local files. Used the existing verified Python 3.12.16/uv 0.13.6 and an external offline cache; no hosted Action or interpreter download was simulated as a pass.
- Results: lock check and fresh locked sync passed; Ruff/format, strict mypy and harness verification passed; all 49 ordinary tests passed with JUnit/coverage XML; isolated source/wheel build and fresh installed-wheel smoke passed. The `not load` selection excluded none of the current tests. App code, tests, dependency manifests/lock and vendored skills were not changed by this task.
- Remaining gate: actual hosted setup, Linux runner execution and artifact upload require an authorized published revision and successful GitHub run/job/artifact evidence. No commit/push/dispatch was performed. T01a remains unchecked and T02 remains dependent on that hosted qualification.
