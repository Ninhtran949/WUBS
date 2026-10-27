# ADR-0002: Reproducible toolchain and lean harness continuity

Date: 2026-10-27. Status: accepted as the SE/SA design baseline under the user's delegated design request; implementation pending. Applies to C02-C04 and F12.

## Context

The lean engineering harness is already installed with six original Addy Osmani skills, shared references, license and pinned provenance. Task.md suggests a broader plugin installation and duplicate task files as a reference approach. The user's current request explicitly allows adapting that suggestion to the existing harness.

The active Python is 3.11.9, while the product requires 3.12+. No product package, lockfile or configured lint/type/test environment exists yet. Those absences must remain visible rather than being called a completed bootstrap.

## Decision

Retain the existing six skills and native Codex discovery, unchanged byte-for-byte. Keep one concise root `AGENTS.md`; detailed rules are task-routed documents. The provenance manifest remains the source of exact upstream commit/hashes. Do not install the entire upstream plugin, duplicate a router, copy skill bodies into root instructions, or add optional skills solely to mirror Task.md.

Use `docs/SPEC.md` for the product contract and one `docs/plans/implementation-plan.md` with its own task checklist. Do not create parallel root `SPEC.md`, `tasks/plan.md` or `tasks/todo.md`. Specification/planning skill defaults are overridden by repository policy.

For future product implementation, select Python 3.12+, `uv` project environments/lockfiles, a minimal setuptools wheel build, standard-library argument parsing, Ruff formatting/lint, strict mypy, pytest/pytest-asyncio and coverage. Keep runtime extras explicit. Routine checks use locked resolution; only deliberate dependency work updates the lock. T01 must choose and test exact compatible versions, and record tool/browser provenance.

## Alternatives and consequences

- Replacing the working harness with the full plugin adds available workflows and global state without meeting a missing current need; rejected for this baseline.
- Unlocked pip installs or a custom set of bootstrap/requirements scripts reduce initial tooling but make repeated environments drift or add maintenance; use one lock workflow instead.
- uv is an additional development tool and is not currently available on the inspected PATH. Bootstrap must establish it and the required Python without claiming that existing harness tests prove product compatibility.
- Existing standard-library harness verification remains usable before product bootstrap. Future product commands are explicitly planned until their environment exists. No installed dependencies, browser capabilities, CI outcomes or product readiness are asserted by this decision.

Sources: [upstream Codex setup](https://github.com/addyosmani/agent-skills/blob/aeac41d4d005999432bb7312f7ff06383a91d59d/docs/codex-setup.md), [uv lock semantics](https://docs.astral.sh/uv/concepts/projects/sync/), [PROJECT](../PROJECT.md), [.agents/upstream.json](../../.agents/upstream.json).
