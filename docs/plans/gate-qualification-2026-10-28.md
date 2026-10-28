# T02 fresh-console and T01a hosted evidence, 2026-10-28

This initially records the investigation before the Owner's subsequent authorization
to commit and push directly to `dev`; historical results below retain that scope.
Product code, tests,
dependencies, workflow and acceptance criteria were preserved. No commit, push,
dispatch, deployment, Windows Security setting or security policy was changed.
Raw machine-local evidence is ignored under `.local/gate-qualification-20261028/`;
the findings below do not depend on those files being shipped in a checkout.

| Gate | Observed result | Remaining condition |
| --- | --- | --- |
| T02 fresh-console smoke | **PASS locally**, using the unchanged required script and real executable | Does not establish hosted or release qualification. |
| T01a hosted CI | **BLOCKED**, zero hosted runs | Authorized publication, then actual successful Ubuntu and Windows jobs with evidence. |

T02's task checkbox remains open because it depends on T01a. Release is **not ready**.
The earlier failed smoke attempts remain recorded in the implementation checkpoint.

## T01a: actual GitHub state

Read-only GitHub checks at 2026-10-28 09:43 UTC returned:

| Evidence | Result |
| --- | --- |
| Repository / Actions dashboard | [Ninhtran949/WUBS Actions](https://github.com/Ninhtran949/WUBS/actions) |
| Remote `main` SHA | `035311b6f66a88839c4616a9954c35f72d99a7ab` |
| Local HEAD SHA | `b040e7fa3722e1397200b32d058168c7571a37fc` |
| Workflow on remote `main` | `.github/workflows/ci.yml` returns HTTP 404. |
| Registered workflows | `total_count: 0` from the [workflow API](https://api.github.com/repos/Ninhtran949/WUBS/actions/workflows?per_page=100). |
| Hosted runs | `total_count: 0`, `workflow_runs: []` from the [run API](https://api.github.com/repos/Ninhtran949/WUBS/actions/runs?per_page=20). |
| Actual run/workflow URL, qualified commit SHA | None available; local HEAD does not contain the prepared workflow. |
| Job status / hosted test results / artifacts | N/A: no jobs have run. |

The [local workflow](../../.github/workflows/ci.yml) has push/PR/manual triggers, read-only repository permissions,
SHA-pinned actions, unpersisted checkout credentials, Ubuntu/Windows matrix jobs,
15-minute timeouts, locked install, lint/format/types, harness, ordinary tests,
isolated build, native-console wheel smoke and narrowly selected artifacts.
`actionlint -no-color .github/workflows/ci.yml` exited 0. Local command results
below establish preparation only; hosted action setup, Linux execution and
artifact upload remain unverified.

The workflow and T02 code are uncommitted changes above local HEAD. An authorized
commit/push must publish the complete reviewed revision, including workflow,
lockfile, source and required documents. A push can then trigger CI; record its
actual run URL and tested commit SHA, successful `Checks (ubuntu-24.04)` and
`Checks (windows-2025)` jobs, test results and `ci-ubuntu-24.04` /
`ci-windows-2025` artifact links before closing T01a. No publication or dispatch
was attempted, and no speculative run URL is presented as evidence.

## T02: controlled launcher comparison

Paths below use `PROJECT = C:\Users\Admin\workspace\WUBS` and
`TEMP = C:\Users\Admin\AppData\Local\Temp`. The normal-directory clean install
was created under the project, outside the system temp directory. Both fresh
environments were absent before creation, installed the seven hashed runtime/project
wheels, passed `uv pip check`, and imported their own `site-packages` with Python
`-I`. All three comparison cases ran with the same CWD outside the source checkout,
at `TEMP\stresslab-gate-t4w9yc6t`, with source-path environment overrides removed.

| Case | Executable path | Full-file SHA-256 | Signature evidence | Result |
| --- | --- | --- | --- | --- |
| Existing project venv | `PROJECT\.venv\Scripts\stresslab.exe` | `997ecb494b9c7109d5e605976a730a998fa630adcbaa027bc15c6ff866732e57` | Authenticode `NotSigned` | Console help/version/static validation exit 0. |
| Fresh normal-directory install | `PROJECT\.local\gate-qualification-20261028\20261028T093012120764Z\project-venv\Scripts\stresslab.exe` | `9645856209345bab481531946ddbd7beebe2cf6df370f0b6e2a1510e7f71c8a3` | Authenticode `NotSigned` | Install/check, module, native console and isolated import exit 0. |
| Fresh temp install | `TEMP\stresslab-gate-t4w9yc6t\temp-venv\Scripts\stresslab.exe` | `b69159c81bd4272230f8a2fce646f97b8f5b8fb526814bb60df799c3888dc488` | Authenticode `NotSigned` | Install/check, module, native console and isolated import exit 0. |
| Earlier blocked temp install | `TEMP\stresslab-wheel-5q6nsmdb\venv\Scripts\stresslab.exe` | `7e085afd6155b0dbb9fda0dab02d601deff24a9c51785f89cc35748fe977b97c` (event 3077 **SHA256 Flat Hash**) | Event 3089: zero signatures, unknown publisher | Native process creation failed with WinError 4551 at 09:03:57 UTC. |

Current executable metadata: all three files are 47,104 bytes, x64 PE machine
`0x8664`, PE timestamp 0, no signer, empty FileVersion/ProductVersion/OriginalFilename/
FileDescription and no `Zone.Identifier` stream. PE section hashes match except
`.pedata`. Their embedded entrypoint calls
`web_stress_lab.interfaces.cli:main`; after the first absolute-interpreter line,
the Python body is identical (SHA-256
`4e851c5d88f914b2454872572ba65e0f6d157eeb2c3e65a1378b301b809ce88d`).
Different interpreter paths account for embedded-entrypoint differences, so full
launcher hashes are not expected to match across environments.

The old blocked file was already removed by its temporary-directory cleanup.
Its PE sections, size and zone stream cannot now be inspected directly. Event
3077 reports blank original filename/description/product and FileVersion
`0.0.0.0`; event 3089 supplies unsigned status. These event fields are not a
reconstructed inspection of the deleted executable. Its CI image SHA-256
`9c71fb64e4ba7179169fd9573720ab284b2a21df0622eecfb999c94c6160fe7e`
is distinct from the **flat** file hash used in the comparison table.

## Windows block diagnosis and limits

`Microsoft-Windows-CodeIntegrity/Operational` was enabled and readable. Correlated
events for the old blocked launcher share an ActivityID:

| UTC time on 2026-10-28 | Event / record | Relevant evidence |
| --- | --- | --- |
| 09:03:57.3082113 | 3033 / 252830 | Requested signing level 2, validated level 1; process was the workspace Python. |
| 09:03:57.3086556 | 3077 / 252832 | Enforced block, policy `VerifiedAndReputableDesktop`, status `0xc0e90002`, matching launcher path and hashes. |
| 09:03:57.3082131 / .3086583 | 3089 / 252831, 252833 | Zero signatures; publisher/issuer unknown. |

Microsoft documents [3077 as an enforced block and 3089 as signature evidence](https://learn.microsoft.com/en-us/windows/security/application-security/application-control/app-control-for-business/operations/event-id-explanations), correlated using ActivityID.
The [Microsoft Windows SDK status header](https://github.com/microsoft/win32metadata/blob/main/generation/WinSDK/RecompiledIdlHeaders/shared/ntstatus.h)
maps `0xc0e90002` to `STATUS_SYSTEM_INTEGRITY_POLICY_VIOLATION`.
This identifies OS enforcement as the cause of that process-creation failure.
No packaging or entrypoint failure was reproduced by the later installations;
both module and real-console paths succeed. No application fix is justified by
the observed block.

The later successful unsigned launchers rule out a universal prohibition on temp
paths or unsigned wrappers. The precise policy decision and reason it changed
are unproven. Read-only `CiTool.exe -lp -json` returned access denied
(`OperationResult: -2147024891`, `0x80070005`), so a complete active-policy inventory
was unavailable at current privileges. No policy modification or security bypass
was attempted. Success is a measured snapshot, not proof this OS limitation can
never recur.

## Executed checks

The comparison used wheel
`.tools/t02-final-dist/web_stress_lab-0.1.0-py3-none-any.whl`, SHA-256
`22a412c9fb2803f8b3b6821b6b41fc7535cee7d7011ce49e384ecffe6348ebcd`.
All ten packaged Python files equal current product source byte-for-byte;
entrypoint, Python requirement and exact Pydantic/PyYAML dependencies match
`pyproject.toml`.

With `UV_CACHE_DIR` set to the workspace `.tools/cache`, this unchanged required
command exited 0 (log completed at 09:33:11 UTC):

```powershell
.tools/uv.exe run --locked --offline python scripts/smoke_wheel.py .tools/t02-final-dist/web_stress_lab-0.1.0-py3-none-any.whl --uv .tools/uv.exe
```

It printed `PASS: installed wheel 0.1.0, hashed locked runtime deps, CLI help/version/static validation, isolated import`.
The script still creates a fresh temporary environment, checks the complete
locked/hashed runtime graph, invokes the actual console and requires isolated
imports. No module fallback, exception waiver, skip or weakened assertion was used.

A final isolated build after the documentation update and its fresh native-console
smoke also exited 0 at 09:47 UTC:

```powershell
.tools/uv.exe build --out-dir .tools/gate-qualification-20261028-dist --python .venv/Scripts/python.exe --offline --no-python-downloads
.tools/uv.exe run --locked --offline python scripts/smoke_wheel.py .tools/gate-qualification-20261028-dist/web_stress_lab-0.1.0-py3-none-any.whl --uv .tools/uv.exe
```

The new wheel SHA-256 is
`22143e0a9d8ed6c472da8953f9e8994de9d467eb51eb664f162a662f1d5558c3`;
the source archive SHA-256 is
`ab7d059220330e4257b3548e461a23277c2239c274744dd52012c709444ab132`.
All ten Python sources match the new wheel; both archives exclude local tools,
environments and report data. Earlier build artifacts were preserved. This smoke
installed all seven hashed wheels, passed dependency checks and executed real
console help/version/static validation and isolated import without a fallback.

| Local Windows check | Actual result |
| --- | --- |
| `uv lock --check --offline` | Exit 0; 23 packages. |
| `uv sync --locked --all-extras --group dev --no-build --no-python-downloads --offline` | Exit 0. |
| Locked/offline Ruff lint and format | Exit 0; 35 files already formatted. |
| Locked/offline `mypy src/` | Exit 0; 10 source files. |
| Locked/offline `python -B scripts/verify_harness.py` | Exit 0; six skills and pinned integrity/layout verified. |
| `actionlint -no-color .github/workflows/ci.yml` | Exit 0. |
| Locked/offline `python -m pytest -q -m 'not load' --cov --cov-report=term-missing --cov-report=xml:.local/gate-qualification-20261028/coverage.xml --junitxml=.local/gate-qualification-20261028/junit.xml` | **192 passed**, zero failures/skips, 97% coverage; 388 statements, 100 branches. |

Raw evidence includes `github-evidence.json`, `console-cases.json` under the
timestamped comparison directory, `launcher-metadata.json`, correlated
CodeIntegrity exports, `original-console-smoke.log`, `local-checks.json`,
`build-smoke.json`, final build/smoke logs, individual command logs, JUnit and
coverage XML. Raw exports and retained
diagnostic environments remain local and ignored.

Final inspection confirmed unchanged HEAD, staged diff and lockfile against the
starting snapshot; only README, PROJECT, the relevant checkpoint and this evidence
report changed in the deliverable. Documentation link and Git whitespace checks
passed. No source/test refactor was needed.

The strict console criterion is met in the observed runs, so no acceptance
change is proposed or applied. If OS enforcement blocks future clean installs,
retain the failure and obtain an Owner-approved environmental/acceptance ruling;
do not silently substitute module execution or mark a blocked console gate PASS.
Hosted CI and release remain unqualified.
