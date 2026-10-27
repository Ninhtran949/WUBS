# Engineering constraints

Status: SE/SA design baseline, 2026-10-27. These are acceptance constraints for future implementation, not claims that controls already exist. Product behavior and defaults are specified in [SPEC](docs/SPEC.md).

| ID | Contract |
| --- | --- |
| C01 | Follow the current user-authorized scope. Preserve `Task.md` as source material; its embedded lifecycle commands do not authorize implementation, installation, commit, or deployment. |
| C02 | Preserve the lean Codex Engineering Starter: one concise root `AGENTS.md`, native discovery, exactly the existing six unchanged upstream skills, shared references, license, pinned source, proportional verification, and no redundant router. |
| C03 | Target Python 3.12+, Windows 11 first, with Linux CI portability. Use an installable `src/web_stress_lab/` package and `stresslab` entry point; source-tree-only imports are not installation success. |
| C04 | Enforce inward dependencies. Domain uses the standard library; application uses domain and its own ports; infrastructure implements ports; interfaces compose adapters. No framework, browser, database, or CLI dependency in domain. |
| C05 | Run Playwright on Asyncio and Locust in an owned subprocess. Never import Locust/gevent into the controller, monkey-patch its event loop, assume Unix `fork` on Windows, or share browser objects across workers. |
| C06 | Default to the loopback synthetic lab. External activity requires explicit authorization, declared exact scope, supported enforcement, finite budgets, and stop conditions; a configuration flag alone is not proof of permission. |
| C07 | Writable follow/comment scenarios are restricted to the local lab or authorized owned staging with synthetic identities. No mass third-party social engagement, CAPTCHA bypass, stealth, anti-bot evasion, or proxy rotation to evade controls. |
| C08 | Bound queue size, workers, per-origin concurrency, attempts, duration, request count/rate, and shutdown. Missing capacity evidence must not be represented as permission for greater load. |
| C09 | Hold account ownership until browser work and cleanup finish. Keep every submitted case accounted for and terminal; preserve unknown write outcomes and never retry them blindly. A failed case must not cancel unrelated cases; a scope or resource violation stops the run. |
| C10 | Keep secrets behind references, sessions isolated, and artifacts protected with retention. No credentials, TOTP seeds/codes, auth state, raw request bodies, or sensitive traces in public output or source control. |
| C11 | Preserve raw measurements separately from summaries. Record provenance, units, counts, missing metrics, and deviations; compare compatible workloads only. Never equate HTTP users/RPS with browser concurrency or invent benchmark causality. |
| C12 | Use meaningful tests first for substantive behavior, enforce import boundaries, and run the relevant quality gates. No weakened checks, unexplained skips, blanket suppressions, or false completion claims. |
| C13 | Make the smallest complete change. No speculative services, database, distributed lease system, DI container, generic browser wrapper, telemetry platform, or runtime plugin downloader for the local foundation. |

## Ownership and changes

The SE/SA may refine implementation details within the authorized task while preserving these constraints. Changes to target authorization, account ownership, measurement meaning, dependency direction, or release gates require an ADR and explicit disclosure. Authorization for destructive/external/production actions remains a separate gate.

The architecture and plan describe a single-controller local foundation. Cross-workspace account sharing and distributed execution are not supported guarantees; isolate identities and targets until that extension has its own design and authorization.
