# Web Stress Lab

Python 3.12+ framework for bounded UI reliability experiments against a synthetic
local target. The implementation is tracked in
[the implementation plan](docs/plans/implementation-plan.md); see
[PROJECT](docs/PROJECT.md) for verified capabilities, commands and limitations.

The initial package provides `stresslab --help` and `stresslab --version`.
Browser, lab and load commands are added only when their implementation gates pass.
External experiments require separate authorization and enforcement.

Use Python 3.12.16 and uv 0.13.6. With uv on PATH, install the locked development
environment and invoke the CLI from the workspace root:

```powershell
uv sync --locked --all-extras --group dev
uv run --locked stresslab --help
uv run --locked stresslab --version
```

In the current workspace, uv is available as `.tools/uv.exe`; the toolchain
provenance and verification commands are recorded in [PROJECT](docs/PROJECT.md).

The [baseline CI workflow](.github/workflows/ci.yml) is prepared for push/PR checks
on Ubuntu and Windows: locked install, lint/format/types, ordinary tests, harness
verification, build and fresh-wheel smoke. Each feature extends that pipeline.
T01a's first successful hosted run remains pending authorized publication; local
checks do not establish hosted CI success. See [PROJECT](docs/PROJECT.md).

