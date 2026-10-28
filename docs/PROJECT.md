# Web Stress Lab (workspace: WUBS)

## Verified state and scope

As of 2026-10-28, [Task.md](../Task.md) supplies requirements for an automated UI reliability and performance testing framework. T01's local bootstrap/review fixes were verified. T01a and T02 are now complete for their declared scope on `dev`: [hosted run 40669673712](https://github.com/Ninhtran949/WUBS/actions/runs/40669673712) passed both Ubuntu and Windows on commit `09dc45d770e641802b400bdfec68f34c63494d04`. Each platform passed 192 ordinary tests (97% coverage), locked lint/format/types, harness, isolated build and the unchanged fresh native-console wheel smoke. T02 provides bounded static YAML/JSON validation into immutable domain values and sanitized human/JSON results. Clean console installs under the local project directory and in temp also pass. This is not whole-foundation or release qualification.

The Owner authorized commits and direct pushes to `origin/dev` to complete T01a and update T02's dependency status. Existing work was preserved and published; `main` remains `035311b6f66a88839c4616a9954c35f72d99a7ab`. No merge, PR or deployment was performed. T03-T20 remain pending and no later feature work was started. There is no local lab, browser engine or Locust adapter yet. See the [gate evidence](plans/gate-qualification-2026-10-28.md) for launcher comparison, Windows events, actual hosted jobs/logs and validated test/build artifacts.

The system Python remains 3.11.9. Workspace-local tools provide CPython 3.12.16, uv 0.13.6, and a Python 3.12.16 `.venv`; no global Python or PATH setting was changed. Dev tools remain mypy 2.4.0, pytest 9.1.1, pytest-asyncio 1.4.1, pytest-cov 7.1.0 and Ruff 0.17.3, with types-PyYAML 6.0.12.20260906 added for strict checking. Runtime dependencies are Pydantic 2.14.1 and PyYAML 6.0.3. `uv.lock` resolves 23 packages including the project and transitive dependencies; setuptools 84.2.1 remains the separate exact build-system pin. The project `.venv` was synchronized with `--locked --no-build`. Baseline Linux/Windows CI is verified; later runtime capabilities remain unverified.

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

`Task.md` remains unchanged and is required by the harness verifier; its `-text` attribute preserves the original bytes across checkouts. Where its recommended harness conflicts with the existing setup, this baseline retains six pinned skills, native discovery, and one plan/checklist under `docs/plans/`. No global plugin installation is required. Proposed code trees are design targets; create files when implementing an actual behavior.

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

The workspace-local toolchain supports the following workflow. T02 qualification used locked runs and the workspace cache; `--offline` was used after provisioning. Both Python-module and real-console entry points pass outside checkout. Historical temporary-launcher failures are correlated with enforced CodeIntegrity policy `VerifiedAndReputableDesktop`; later clean project/temp installs and the original smoke pass without application or security-policy changes. The reason for the changed allow/block decision is unproven. Exact results are in the plan checkpoint and gate evidence.

```powershell
$env:UV_CACHE_DIR = Join-Path $PWD '.tools/cache'
.tools/uv.exe sync --locked --all-extras --group dev --no-build --no-python-downloads --offline
.tools/uv.exe run --locked --offline python -m web_stress_lab validate-config fixtures/experiments/local-browser.yaml --json
.tools/uv.exe run --locked --offline python -m web_stress_lab validate-config fixtures/experiments/local-http.json --json
.tools/uv.exe run --locked --offline ruff check .
.tools/uv.exe run --locked --offline ruff format --check .
.tools/uv.exe run --locked --offline mypy src/
.tools/uv.exe run --locked --offline python -m pytest -q -m 'not load' --cov --cov-report=term-missing --cov-report=xml:artifacts/coverage.xml --junitxml=artifacts/junit.xml
.tools/uv.exe build --out-dir '.tools/t02-final-dist' --python '.venv/Scripts/python.exe' --offline --no-python-downloads
```

The build uses an isolated environment with the pinned setuptools backend. Existing `dist/` artifacts denied access/overwrite (WinError 5); T02 qualification used fresh output directories under `.tools/`, preserving the old artifacts. The build's local-cache warning is checked by archive inspection.

The updated `scripts/smoke_wheel.py` exports the complete runtime graph from `uv.lock`, adds the built wheel's SHA-256, installs only hashed prebuilt wheels offline, and runs `uv pip check` before invoking the real console. `--no-deps` uses the already-complete export and avoids uncached PEP 658 metadata requests; it does not omit the graph check. The required script passes locally and on both hosted platforms. A fresh cache requires registry data as well as wheel content: the workflow explicitly exports and reinstalls the complete hashed runtime graph online before the unchanged offline smoke. A cold-cache regression reproduced the failure before provisioning and passed afterward. Earlier WinError 4551 failures remain historical evidence; no fallback, skip, acceptance change or Windows security-policy modification was introduced. Separate module diagnostics do not substitute for console acceptance.

## Toolchain provenance and lock verification

uv was downloaded from its [official 0.13.6 release](https://github.com/astral-sh/uv/releases/tag/0.13.6), with archive SHA-256 `a2a8820d5eea32f08ef467ef3b7f66883a9b076d5737a2fc2fbb5f458d1bb50f` verified against the release checksum. CPython came from the [official python-build-standalone 20261026 release](https://github.com/astral-sh/python-build-standalone/releases/tag/20261026), archive `cpython-3.12.16+20261026-x86_64-pc-windows-msvc-install_only_stripped.tar.gz`, SHA-256 `1f2ab53880fc67ea323398c6388e05af28addc99a8e389209f08a51fdff4b149` verified against `SHA256SUMS`. Only the interpreter archive and uv executable were extracted; no remote installer was executed or Windows Python registration changed.

The initial offline bootstrap used seventeen development/backend wheels downloaded with curl from official PyPI file URLs and checked against PyPI JSON SHA-256 metadata. The reviewed startup files were setuptools' `distutils-precedence.pth` and coverage's `a1_coverage.pth`; Ruff's executable is its packaged CLI. T02 added six reviewed/hash-verified PyPI wheels: annotated-types 0.8.0, Pydantic 2.14.1, pydantic-core 2.50.1, PyYAML 6.0.3, types-PyYAML 6.0.12.20260906 and typing-inspection 0.4.4. None contained `.pth` or install-script entries. The boundary uses [Pydantic strict validation](https://docs.pydantic.dev/latest/concepts/strict_mode/) and [PyYAML SafeLoader](https://pyyaml.org/wiki/PyYAMLDocumentation), with additional duplicate/alias/tag/size/depth checks. No third-party source build was executed. Local metadata, wheels, toolchain and cache remain ignored under `.tools/`; no browser is installed.

uv 0.13.6 generated and updated `uv.lock` against `https://pypi.org/simple` using Python 3.12.16 and `--no-build --no-python-downloads`. T02 preserves the existing pins and adds its six packages. Review confirms official PyPI registry/file URLs, hashes and no Git/path overrides; `uv lock --check --offline` passes. The T01 lock digest remains historical evidence in its checkpoint, not the current T02 digest. Fresh installs need network access or an appropriately populated cache; ignored caches are not part of the checkout.

## Toolchain workflow and future runtime dependencies

The target remains Python 3.12+, Asyncio, Playwright, pytest, and a managed Locust subprocess, as requested by `Task.md`. Boundary-only Pydantic/PyYAML validation is now implemented. Browser, lab, load, TOTP and protected-state capabilities remain later tasks. See [ADR-0001](adr/0001-local-runtime-and-boundaries.md) and [ADR-0002](adr/0002-toolchain-and-harness-continuity.md); browser revisions and compatibility have not yet been selected or tested.

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

T01a is **PASS** on `dev` at `09dc45d770e641802b400bdfec68f34c63494d04`: [run 40669673712](https://github.com/Ninhtran949/WUBS/actions/runs/40669673712), successful `Checks (ubuntu-24.04)` and `Checks (windows-2025)`, 192 tests each with zero failures/errors/skips, passing native-console smoke and uploaded artifacts. Both artifact ZIPs were downloaded, matched against API SHA-256 digests and inspected for JUnit, coverage, wheel and source archive. The initial failed hosted run is retained as history; its missing registry-cache data was fixed by explicit hashed provisioning, without changing product code, tests, lockfile or smoke assertions. Gitleaks scans of the publication tree, existing history and staged revisions found zero secrets. `main` is unchanged and no PR, merge or deployment occurred. See [gate evidence](plans/gate-qualification-2026-10-28.md), [plan](plans/implementation-plan.md) and [ADR-0003](adr/0003-ci-at-bootstrap.md).

Future capabilities extend this workflow when implemented. Browser provisioning and new required local tests arrive with their feature; expensive load/soak qualification is separately selected. T19 qualifies the full accumulated pipeline.

## Skills and provenance

The six requested skills are unchanged copies from [Addy Osmani's agent-skills](https://github.com/addyosmani/agent-skills). [.agents/upstream.json](../.agents/upstream.json) records the exact commit, archive digest, source paths, and file hashes; [.agents/LICENSE](../.agents/LICENSE) preserves the original upstream license for those files.

Shared references remain in `.agents/references/` and skill-local references retain their original relative paths. `.gitattributes` prevents Git text conversion of vendored files. To reproduce the installation, copy only the manifest's source files from its pinned archive to their recorded destination paths, without decoding or rewriting their bytes, then run the checks above. Updates require reviewing and repinning the source and rerunning verification.

Codex discovers `.agents/skills/` natively; see the [official skill documentation](https://learn.chatgpt.com/docs/build-skills). Launch from the workspace root. Global/plugin skills are outside the repository installation; do not install additional packs to satisfy names mentioned in `Task.md` or upstream examples.
