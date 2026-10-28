# Web Stress Lab

Python 3.12+ framework for bounded UI reliability experiments against a synthetic
local target. The implementation is tracked in
[the implementation plan](docs/plans/implementation-plan.md); see
[PROJECT](docs/PROJECT.md) for verified capabilities, commands and limitations.

The package provides `stresslab --help`, `stresslab --version` and static
`stresslab validate-config <file> --json` validation for bounded local experiments.
Browser, lab and load commands are added only when their implementation gates pass.
External experiments require separate authorization and enforcement.

Use Python 3.12.16 and uv 0.13.6. With uv on PATH, install the locked development
environment and invoke the CLI from the workspace root:

```powershell
uv sync --locked --all-extras --group dev
uv run --locked stresslab --help
uv run --locked stresslab --version
uv run --locked stresslab validate-config fixtures/experiments/local-browser.yaml --json
uv run --locked stresslab validate-config fixtures/experiments/local-http.json --json
```

In the current workspace, uv is available as `.tools/uv.exe`; the toolchain
provenance and verification commands are recorded in [PROJECT](docs/PROJECT.md).

Validation reads only the config file, creates no reports and does not resolve
secrets or start an engine. The examples declare future `LOGIN`/`HTTP_HEALTH`
workloads; they do not establish runtime readiness or validate catalog contents.
See the [T02 input contract](docs/SPEC.md#t02-static-configuration-contract).
T02's fresh installed-console smoke passed on 2026-10-28, including clean installs
under the project directory and in temp. The earlier Windows Application Control
block is documented in the [gate evidence](docs/plans/gate-qualification-2026-10-28.md).
T01a and T02 are complete for their declared scope on `dev`; later runtime
capabilities and full release qualification remain pending.

T03 adds a strict JSON account-catalog API, deterministic ID filtering and an
explicit environment secret provider. The [synthetic catalog](fixtures/experiments/accounts.synthetic.json)
contains references only; set synthetic values in the process environment.
See the [T03 contract](docs/SPEC.md#t03-identity-catalog-and-secret-references)
and [API usage](docs/PROJECT.md#identity-catalog-and-secret-provider-apis).
This new revision has not been published or qualified by hosted CI.

The [baseline CI workflow](.github/workflows/ci.yml) is prepared for push/PR checks
on Ubuntu and Windows: locked install, lint/format/types, ordinary tests, harness
verification, build and fresh-wheel smoke. Each feature extends that pipeline.
T01a passed [hosted CI run 40669673712](https://github.com/Ninhtran949/WUBS/actions/runs/40669673712)
on Ubuntu and Windows: 192 tests per platform, build, offline installed-console
smoke and test/build artifacts. See [PROJECT](docs/PROJECT.md).

