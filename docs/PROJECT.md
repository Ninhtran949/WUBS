# Web Stress Lab (workspace: WUBS)

## Verified state and scope

As of 2026-10-27, [Task.md](../Task.md) supplies requirements for an automated UI reliability and performance testing framework. T01 implementation provides an installable `src/web_stress_lab/` package, `pyproject.toml`, `stresslab --help`/`--version`, import-boundary tests and configured quality tools. A built wheel was installed and exercised in a fresh environment outside the checkout. The original six-skill harness remains verified. Git metadata is absent.

The Owner now authorizes development according to the existing plan. T01 is **in progress, not complete**: sandbox networking prevents uv from resolving PyPI metadata and generating `uv.lock`. Escalation was rejected by the session approval policy. An offline retry confirmed that registry metadata is not cached. T02-T20 remain pending behind that dependency gate. There is no local lab, browser engine, Locust adapter or product CI yet; commits, pushes, deployment and external load remain unauthorized.

The system Python remains 3.11.9. Workspace-local tools now provide CPython 3.12.16, uv 0.13.6, and a Python 3.12.16 `.venv`; no global Python or PATH setting was changed. Dev tools are mypy 2.4.0, pytest 9.1.1, pytest-asyncio 1.4.1, pytest-cov 7.1.0, and Ruff 0.17.3; the build backend is setuptools 84.2.1. They were installed offline from reviewed, hash-verified wheels, **not from a lockfile**. This establishes local functional evidence without establishing reproducible locked installation.

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

`Task.md` remains unchanged. Where its recommended harness conflicts with the existing setup, this baseline retains six pinned skills, native discovery, and one plan/checklist under `docs/plans/`. No global plugin installation is required. Proposed code trees are design targets; create files when implementing an actual behavior.

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

The existing workspace environment also supports these commands, executed during T01:

```powershell
.venv/Scripts/stresslab.exe --help
.venv/Scripts/stresslab.exe --version
.venv/Scripts/python.exe -m pytest -q --cov --cov-report=term-missing
.venv/Scripts/ruff.exe check .
.venv/Scripts/ruff.exe format --check .
.venv/Scripts/mypy.exe src/
$env:UV_CACHE_DIR = Join-Path $PWD '.tools/cache'
.tools/uv.exe build --python '.venv/Scripts/python.exe' --offline --no-build-isolation
.venv/Scripts/python.exe scripts/smoke_wheel.py dist/web_stress_lab-0.1.0-py3-none-any.whl --uv .tools/uv.exe
```

The build uses the already installed, pinned backend. Wheel smoke uses an empty temporary environment, installs the built wheel with `--offline --no-deps`, invokes the actual console script, and verifies an isolated import from `site-packages`. It establishes the current dependency-free CLI only. The build warned that the workspace-local cache might enter the source distribution; inspecting both built archives confirmed it did not. These commands do not substitute for the pending locked-install gate.

## Toolchain provenance and pending bootstrap gate

uv was downloaded from its [official 0.13.6 release](https://github.com/astral-sh/uv/releases/tag/0.13.6), with archive SHA-256 `a2a8820d5eea32f08ef467ef3b7f66883a9b076d5737a2fc2fbb5f458d1bb50f` verified against the release checksum. CPython came from the [official python-build-standalone 20261026 release](https://github.com/astral-sh/python-build-standalone/releases/tag/20261026), archive `cpython-3.12.16+20261026-x86_64-pc-windows-msvc-install_only_stripped.tar.gz`, SHA-256 `1f2ab53880fc67ea323398c6388e05af28addc99a8e389209f08a51fdff4b149` verified against `SHA256SUMS`. Only the interpreter archive and uv executable were extracted; no remote installer was executed or Windows Python registration changed.

Seventeen development/backend wheels were downloaded with curl from official PyPI file URLs and checked against PyPI JSON SHA-256 metadata. The reviewed startup files were setuptools' `distutils-precedence.pth` and coverage's `a1_coverage.pth`; Ruff's executable is its packaged CLI. No third-party source build was executed. Local download metadata, checksums, wheels, Python, uv and the uv cache live under ignored `.tools/`; installed packages live under ignored `.venv/`. These caches are local recovery aids, not a portable dependency lock. No product runtime dependency or browser is installed.

To close T01 in an environment where uv can access PyPI, use uv 0.13.6 and Python 3.12.16 to run the deliberate `uv lock --no-build` resolution, review `uv.lock`, then execute all locked gates below and the wheel smoke again. Do not hand-edit a lockfile or label the current offline install reproducible.

## Planned product toolchain

The target remains Python 3.12+, Asyncio, Playwright, pytest, and a managed Locust subprocess, as requested by `Task.md`. The SE/SA baseline chooses `uv` with `pyproject.toml` and `uv.lock`, a standard-library CLI, boundary-only Pydantic/PyYAML validation, and a packaged FastAPI lab. See [ADR-0001](adr/0001-local-runtime-and-boundaries.md) and [ADR-0002](adr/0002-toolchain-and-harness-continuity.md). Bootstrap tool versions are now recorded above; product runtime dependencies, browser revisions and browser compatibility have not yet been selected or tested.

These locked commands remain **planned, not executed**. T01 must generate and verify the lockfile before they become available. Add runtime extras when their tasks implement a capability; no placeholder dependencies or empty production layers are included:

```powershell
uv sync --locked --all-extras --group dev
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy src/
uv run --locked python -m pytest -q
uv build
```

`uv lock` is the deliberate dependency-resolution step when creating or changing the lockfile; routine checks must fail on a stale lock instead of silently upgrading it. Dependencies, Python, uv, and browser revisions must be recorded when established. Browser binaries are a separate provisioned capability; missing browsers must fail the required E2E gate visibly.

## Skills and provenance

The six requested skills are unchanged copies from [Addy Osmani's agent-skills](https://github.com/addyosmani/agent-skills). [.agents/upstream.json](../.agents/upstream.json) records the exact commit, archive digest, source paths, and file hashes; [.agents/LICENSE](../.agents/LICENSE) preserves the original upstream license for those files.

Shared references remain in `.agents/references/` and skill-local references retain their original relative paths. `.gitattributes` prevents Git text conversion of vendored files. To reproduce the installation, copy only the manifest's source files from its pinned archive to their recorded destination paths, without decoding or rewriting their bytes, then run the checks above. Updates require reviewing and repinning the source and rerunning verification.

Codex discovers `.agents/skills/` natively; see the [official skill documentation](https://learn.chatgpt.com/docs/build-skills). Launch from this directory while it has no Git root. Global/plugin skills are outside the repository installation; do not install additional packs to satisfy names mentioned in `Task.md` or upstream examples.
