# Web Stress Lab (workspace: WUBS)

## Verified state and scope

As of 2026-10-27, [Task.md](../Task.md) supplies requirements for an automated UI reliability and performance testing framework. T01 is complete on Windows after the Owner's review fixes: an installable `src/web_stress_lab/` package, `pyproject.toml`, reviewed `uv.lock`, `stresslab --help`/`--version`, import-boundary tests and configured quality tools. The current suite passes 49 tests, including scanner regressions for package-root modules, exact workload namespace boundaries and required source-document presence. Locked quality gates, an isolated-backend build and fresh installed-wheel smoke passed. The original six-skill harness remains verified. Git metadata is present; this task did not initialize Git.

The current request (2026-10-28) adds baseline CI immediately after T01, before T02. The earlier sandbox network block was resolved through approved network access for uv's lock and clean-sync commands. The workflow is prepared locally; T01a remains pending actual hosted qualification. T02-T20 remain pending behind that gate. There is no configuration validator, local lab, browser engine or Locust adapter yet; commits, pushes, deployment and external load remain unauthorized.

The system Python remains 3.11.9. Workspace-local tools provide CPython 3.12.16, uv 0.13.6, and a Python 3.12.16 `.venv`; no global Python or PATH setting was changed. Dev tools are mypy 2.4.0, pytest 9.1.1, pytest-asyncio 1.4.1, pytest-cov 7.1.0, and Ruff 0.17.3. `uv.lock` pins all 16 dev dependencies and the local package; the build backend is pinned separately to setuptools 84.2.1 in `pyproject.toml`. A new `.tools/t01-locked-env` and the existing `.venv` were both successfully synchronized with `--locked`. Linux execution, hosted CI and later product capabilities are unverified.

## Document ownership

| Document | Owns |
| --- | --- |
| [CONSTRAINTS](../CONSTRAINTS.md) | Persistent engineering and safety constraints. |
| [SPEC](SPEC.md) | Capabilities, observable contracts, defaults, and acceptance criteria. |
| [ARCHITECTURE](ARCHITECTURE.md), [ADRs](adr/README.md) | Dependency boundaries, runtime ownership, and consequential design choices. |
| [CONVENTIONS](CONVENTIONS.md) | Coding, testing, quality gates, and agent handoff conventions. |
| [SECURITY](SECURITY.md) | Threats, enforcement, sensitive artifacts, and authorization gates. |
| [EXPERIMENT-METHODOLOGY](EXPERIMENT-METHODOLOGY.md) | Measurement definitions, reproducibility, and comparison rules. |
| [RESEARCH](RESEARCH.md) | Official-source evidence and adopt/adapt/reject rationale. |
| [Implementation plan](plans/implementation-plan.md) | Dependency-ordered work, verification, and execution checkpoints. |

`Task.md` remains unchanged and is required by the harness verifier. It is included in the Git index for source handoff; its `-text` attribute preserves the original bytes across checkouts. A commit is still needed before the current HEAD/archive contains this addition. Where its recommended harness conflicts with the existing setup, this baseline retains six pinned skills, native discovery, and one plan/checklist under `docs/plans/`. No global plugin installation is required. Proposed code trees are design targets; create files when implementing an actual behavior.

## Commands available now

The existing harness verifier and tests use only the Python standard library and were verified with Python 3.11.9. Run from the workspace root:

```powershell
python -B scripts/verify_harness.py
python -B -m unittest discover -s tests -p test_harness.py -v
```

For an independent byte comparison, download the pinned ZIP at `archive.url` in [.agents/upstream.json](../.agents/upstream.json), then run:

```powershell
python -B scripts/verify_harness.py --archive 'PATH-TO-DOWNLOADED-ZIP'
```

The verifier checks the six permitted skills, upstream hashes, local reference paths, and required harness layout. With `--archive`, it also checks the archive digest, selected source-file inventory, and byte equality. It reads local files and never downloads or executes upstream code.

The workspace-local toolchain supports the following workflow. T01 qualification used locked runs and the workspace cache; `--offline` was used after provisioning to ensure the checks needed no further network access. Exact results are in the plan checkpoint.

```powershell
$env:UV_CACHE_DIR = Join-Path $PWD '.tools/cache'
.tools/uv.exe sync --locked --all-extras --group dev --no-build --no-python-downloads --offline
.tools/uv.exe run --locked --offline stresslab --help
.tools/uv.exe run --locked --offline stresslab --version
.tools/uv.exe run --locked --offline ruff check .
.tools/uv.exe run --locked --offline ruff format --check .
.tools/uv.exe run --locked --offline mypy src/
.tools/uv.exe run --locked --offline python -m pytest -q --cov --cov-report=term-missing
.tools/uv.exe build --python '.venv/Scripts/python.exe' --offline --no-python-downloads
.tools/uv.exe run --locked --offline python scripts/smoke_wheel.py dist/web_stress_lab-0.1.0-py3-none-any.whl --uv .tools/uv.exe
```

The build uses an isolated environment with the pinned setuptools backend. Wheel smoke uses an empty temporary environment, installs the built wheel with `--offline --no-deps`, invokes the actual console script, and verifies an isolated import from `site-packages`. It establishes the current dependency-free CLI only; T02 must provision locked runtime dependencies when adding them. The build warned that the workspace-local cache might enter the source distribution; inspecting both built archives confirmed it did not.

## Toolchain provenance and lock verification

uv was downloaded from its [official 0.13.6 release](https://github.com/astral-sh/uv/releases/tag/0.13.6), with archive SHA-256 `a2a8820d5eea32f08ef467ef3b7f66883a9b076d5737a2fc2fbb5f458d1bb50f` verified against the release checksum. CPython came from the [official python-build-standalone 20261026 release](https://github.com/astral-sh/python-build-standalone/releases/tag/20261026), archive `cpython-3.12.16+20261026-x86_64-pc-windows-msvc-install_only_stripped.tar.gz`, SHA-256 `1f2ab53880fc67ea323398c6388e05af28addc99a8e389209f08a51fdff4b149` verified against `SHA256SUMS`. Only the interpreter archive and uv executable were extracted; no remote installer was executed or Windows Python registration changed.

The initial offline bootstrap used seventeen development/backend wheels downloaded with curl from official PyPI file URLs and checked against PyPI JSON SHA-256 metadata. The reviewed startup files were setuptools' `distutils-precedence.pth` and coverage's `a1_coverage.pth`; Ruff's executable is its packaged CLI. The generated lock's 16 dev wheel hashes matched those reviewed artifacts; setuptools remains an exact build-system pin. No third-party source build was executed. Local download metadata, checksums, wheels, Python, uv and the uv cache live under ignored `.tools/`; installed packages live under ignored `.venv/`. No product runtime dependency or browser is installed.

uv 0.13.6 generated `uv.lock` against `https://pypi.org/simple` using Python 3.12.16 and `--no-build --no-python-downloads`. Review confirmed official PyPI registry/file URLs, SHA-256 hashes and the expected dependency graph. A new environment was installed with `sync --locked --all-extras --group dev --no-build --no-python-downloads`; the subsequent locked sync of `.venv` also passed offline. `uv lock --check --offline` passed and left the lock unchanged. Lock SHA-256 at qualification: `a13650271c8c0b306f1ae97ff15ebaab2fe4eb3b72c88d659c19848471ca4524`. Fresh installs need network access or an appropriately populated cache; the ignored local caches are not part of the checkout.

## Toolchain workflow and future runtime dependencies

The target remains Python 3.12+, Asyncio, Playwright, pytest, and a managed Locust subprocess, as requested by `Task.md`. The SE/SA baseline chooses `uv` with `pyproject.toml` and `uv.lock`, a standard-library CLI, boundary-only Pydantic/PyYAML validation, and a packaged FastAPI lab. See [ADR-0001](adr/0001-local-runtime-and-boundaries.md) and [ADR-0002](adr/0002-toolchain-and-harness-continuity.md). Bootstrap tool versions are now recorded above; product runtime dependencies, browser revisions and browser compatibility have not yet been selected or tested.

With uv on PATH, the standard workflow is below; equivalent workspace-local commands were verified above. Add runtime extras when their tasks implement a capability; no placeholder dependencies or empty production layers are included:

```powershell
uv sync --locked --all-extras --group dev
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy src/
uv run --locked python -m pytest -q
uv build
```

`uv lock` is the deliberate dependency-resolution step when creating or changing the lockfile; routine checks must fail on a stale lock instead of silently upgrading it. Dependencies, Python, uv, and browser revisions must be recorded when established. Browser binaries are a separate provisioned capability; missing browsers must fail the required E2E gate visibly.

## Baseline CI and hosted evidence

[.github/workflows/ci.yml](../.github/workflows/ci.yml) is configured for every push, pull request update and manual dispatch. It defines `Checks (ubuntu-24.04)` and `Checks (windows-2025)` with uv 0.13.6 and the Python version in `.python-version`, locked dependency installation, Ruff/format, strict mypy, harness integrity, ordinary non-load pytest/coverage/JUnit results, isolated distributions and fresh installed-wheel smoke.

The workflow has read-only repository permissions, SHA-pinned actions, no persisted checkout credentials, cancellation of superseded runs and a 15-minute timeout per matrix job. Generated test XML and distributions are uploaded as `ci-ubuntu-24.04` / `ci-windows-2025` artifacts with seven-day retention when available; other traces, auth state and local tool caches are not uploaded.

No hosted run has been executed by this change. Workflow validation and local Windows checks establish preparation only. T01a closes after an authorized published revision produces both successful hosted jobs and recorded run/commit/artifact evidence. The publication must include `uv.lock` and the required source documents, including staged `Task.md`; preparing this workflow does not authorize a commit/push. See [plan](plans/implementation-plan.md) and [ADR-0003](adr/0003-ci-at-bootstrap.md).

Future capabilities extend this workflow when implemented. Browser provisioning and new required local tests arrive with their feature; expensive load/soak qualification is separately selected. T19 qualifies the full accumulated pipeline.

## Skills and provenance

The six requested skills are unchanged copies from [Addy Osmani's agent-skills](https://github.com/addyosmani/agent-skills). [.agents/upstream.json](../.agents/upstream.json) records the exact commit, archive digest, source paths, and file hashes; [.agents/LICENSE](../.agents/LICENSE) preserves the original upstream license for those files.

Shared references remain in `.agents/references/` and skill-local references retain their original relative paths. `.gitattributes` prevents Git text conversion of vendored files. To reproduce the installation, copy only the manifest's source files from its pinned archive to their recorded destination paths, without decoding or rewriting their bytes, then run the checks above. Updates require reviewing and repinning the source and rerunning verification.

Codex discovers `.agents/skills/` natively; see the [official skill documentation](https://learn.chatgpt.com/docs/build-skills). Launch from the workspace root. Global/plugin skills are outside the repository installation; do not install additional packs to satisfy names mentioned in `Task.md` or upstream examples.
