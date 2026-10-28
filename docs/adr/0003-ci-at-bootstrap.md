# ADR-0003: Baseline CI at bootstrap

Date: 2026-10-28. Status: accepted by the Owner's request to revise the plan/workflow; hosted qualification pending. Applies to C12 and F12.

## Context

The package, locked toolchain and automated checks already exist. The earlier plan grouped all CI with final product qualification in T19, delaying automation of checks that could already run. The Owner requires an early baseline that grows with the code.

## Decision

Introduce T01a immediately after T01 and before T02. The push/PR/manual workflow runs ordinary checks on Ubuntu and Windows from the lockfile: lint, format, types, harness, tests, isolated build and fresh-wheel smoke. Use pinned actions, read-only repository permissions, no persisted checkout credentials, bounded jobs and narrowly selected evidence artifacts.

Each new capability adds its CI setup and required tests in the same change. Expensive load/soak experiments remain explicitly selected; ordinary regressions cannot be relabeled to avoid the baseline. T19 qualifies the complete accumulated pipeline and operational instructions.

## Evidence and consequences

Local workflow validation is preparation. T01a remains pending until an authorized published revision yields both successful hosted matrix jobs with the run URL, commit SHA and test/build artifacts recorded. This decision does not authorize commit, push, deployment, production access or external load.

This adds early platform feedback without introducing an application service or altering runtime architecture. The small matrix may run for both a branch push and its PR update; prefer that coverage over omitting checks on feature-branch pushes.

Sources: [GitHub workflow triggers](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow), [DORA continuous integration](https://dora.dev/capabilities/continuous-integration/), [implementation plan](../plans/implementation-plan.md).
