# ADR-0001: Local runtime and dependency boundaries

Date: 2026-10-27. Status: accepted as the SE/SA design baseline under the user's delegated design request; implementation pending. Applies to F01-F12.

## Context

Task.md requests Windows-first Python, Asyncio/Playwright, a separate Locust process, a synthetic lab and Clean Architecture. The repository currently has only its harness and design material. Full framework wrappers, distributed infrastructure and a literal class/file for every suggested role would add cost without validating the risky lifecycles.

## Decision

Use one installable `src/web_stress_lab/` package with domain, application, infrastructure and interfaces. Application owns use cases and typed ports; framework/browser/storage implementations depend inward. An explicit composition root constructs concrete dependencies.

Use one local controller/event loop per run, an OS-held exclusive local run lock, in-process identity leases, an owned Locust subprocess and an independent single-process FastAPI lab. Lab fixture state is in memory; reports are append-only raw files with atomic derived outputs. No database, broker or distributed leasing is selected for the foundation.

Put Playwright-dependent scenario plugins under `infrastructure/browser/scenarios/`, using the real async API; do not leak Page types inward or duplicate the locator API. Treat BrowserManager/ContextFactory/AuthProvider and other names in the brief as responsibilities rather than mandatory separate abstractions.

Package the self-contained lab at `src/web_stress_lab/lab_app/` with its own resources. This deliberately adapts the suggested root `lab_app/` so installed CLI operation does not depend on the source CWD. The lab imports no controller internals.

## Alternatives and consequences

- A flat all-in-one script is initially smaller but mixes safety policy, browser lifecycle and reporting and makes ownership tests harder; rejected.
- Several services, a database-backed scheduler, dynamic plugin distribution or a generic automation abstraction would support unrequested scale at a larger operational/testing cost; deferred until a concrete requirement.
- The chosen design needs real boundary, lock, cancellation and subprocess tests. Process-local leases do not guarantee account exclusivity across separate workspaces or distributed hosts; those environments must use isolated identities until designed separately.
- A local pass does not qualify Windows fork-based multiprocessing, external egress containment, or production operation. Those limits remain explicit in SECURITY and the plan.

Evidence and exact dependencies: [RESEARCH](../RESEARCH.md). Authoritative structure and ownership: [ARCHITECTURE](../ARCHITECTURE.md). Changing dependency direction, persistence/distribution model or ownership semantics requires a superseding ADR.
