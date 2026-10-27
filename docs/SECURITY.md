# Security and operational safety

Status: design requirements, not implemented controls. Applies to F01-F10 and constraints C05-C11. Default execution uses synthetic identities and the local lab. This document owns threat/enforcement details; the [SPEC](SPEC.md) owns capability/default contracts.

## Trust boundaries and threats

| Boundary / threat | Required control | Required negative evidence |
| --- | --- | --- |
| Experiment/account files: malformed data, arbitrary code or command injection | Safe YAML loading, Pydantic unknown-field/finite-value validation, registered scenario IDs, fixed executable/module, argument lists, validated paths. No dynamic import/eval from config. | Unsafe YAML tags, shell metacharacters, unknown IDs, duplicate accounts, NaN/Infinity, oversized/out-of-bound settings, malicious path. |
| Target/network: unauthorized traffic, redirect/DNS/proxy scope escape | Exact normalized origin/capability policy before execution, interception where supported, independently enforced egress for external mode, bounded rates and deadlines. | Cross-origin redirect, subresource, service worker, popup, WebSocket, private/metadata destination and proxy bypass cases. |
| Identity: leaked secrets, shared auth, verification challenges | Reference-only metadata, scoped secret resolution, isolated contexts, protected optional auth state with expiry, BLOCKED challenge outcome. | No secret access before admission; no cross-identity cookies; missing/expired/revoked state; challenge produces no retry storm. |
| Writes: duplicate or misattributed follow/comment | Server-side synthetic ownership, stable operation IDs, atomic deduplication/state assertion and reconciliation before retry. | Timeout after server commit, replay, cancellation, wrong-owner mutation/reset, stale lease token. |
| Concurrency/processes: runaway work or leaked children | Bounded admission/backpressure, account ownership through cleanup, OS-held local run lock, cooperative stop and owned-process deadlines. | Two local controllers, queue saturation, browser crash, cancellation in cleanup, orphan child, missing metrics at elevated load. |
| Files/artifacts: traversal, overwrite, report XSS or secret retention | Exclusive contained output paths, safe report escaping, redacted event fields, protected auth/artifact storage, bounded retention. | `../`, absolute/device paths, symlink/junction escape, same run ID collision, HTML payload, disk full, sensitive failure payload. |
| Dependencies/plugins: supply-chain execution or drift | Reviewed pinned dependency graph and build hooks, preserved upstream skill hashes, no config-selected third-party code, security review before release. | Stale lock fails; changed upstream bytes fail; pending unsafe build hook prevents installation. |

## Authorization and target gate

An external configuration must identify the authorized owner/scope reference and expiry, exact origins, allowed scenario capabilities, synthetic account catalog, duration, users/concurrency, request count/rate, resource/error stop thresholds, and artifact policy. The operator also needs explicit authorization for that activity; this declaration does not establish ownership or legal permission on its own.

Allowed modes are local synthetic lab, authorized owned staging, and explicitly authorized external read-only scenarios. State-changing TEST_FOLLOW/TEST_COMMENT can run only in the first two. Scenario mutability comes from the trusted registry, never from a user-supplied `read_only: true` claim.

Reject scope violations before resolving credentials or launching an engine. Never infer an allowlist from a hostname suffix, a proxy setting, successful DNS lookup, or a YAML `authorized` flag. Normalize ports/hosts and reject credentials in URLs and unsupported protocols. External TLS verification stays enabled.

Browser request routing is defense in depth, not proof of network containment: redirects, service workers, WebSockets and DNS changes need explicit tests and a supported egress boundary. The lab serves its own assets and uses a fixed loopback target. Keep external execution disabled until the selected browser/HTTP transport has demonstrated all relevant enforcement paths. Unsupported profiles fail visibly; they must not downgrade to a less protected network mode. A user-declared proxy is not permission to evade controls.

External execution is conditional product work, not part of routine CI or an implicit follow-on from the local plan. A scope violation, invalid/expired authorization, exceeded hard resource budget, failed limiter, or compromised isolation stops admission and begins bounded shutdown. Emergency stopping preserves the reason, terminal case accounting, and unknown effects.

## Secrets, sessions and artifacts

- Initially resolve only explicit environment references for synthetic identities. Never print values, TOTP seeds/codes, cookies, tokens, raw storage state, request bodies, or raw exception strings that can embed them. Sanitize at emission and before persistence; reports use run-scoped account pseudonyms.
- Use a private run-local HMAC key for account pseudonyms; do not export that key with results. Keep references/configuration sanitized and record only approved metadata. Avoid raw usernames in events and artifact filenames.
- Fresh contexts are the default. Optional persisted sessions require explicit consent, account/origin/profile binding, expiry checks, restrictive filesystem access verified on the host, and cleanup. If protected storage cannot be established, persistence is unavailable; no plaintext fallback.
- On-failure screenshots/traces are enabled for the synthetic lab by default. For staging/external targets, capture only with an explicit permitted artifact policy and protected location. A trace/screenshot cannot be assumed redacted because the JSON logs are redacted.
- Apply the SPEC retention policy to artifacts, with owned-path checks and an explicit cleanup operation. Cleanup must never traverse an arbitrary user-supplied directory or delete prior reports to make a run pass. Do not automatically purge forensic evidence after an ambiguous write or security failure.
- Plan Git ignores for `.env*` (except placeholder `.env.example`), `.venv/`, `.local/`, `reports/`, browser auth state, traces, screenshots and temporary logs. Synthetic committed fixtures contain no real secret values. Review diffs before any separately authorized commit.

## Lab and mutation boundary

Bind the lab to loopback. Reset/error/latency controls require test-only authorization and a run fixture namespace; request bodies cannot reset another run or select arbitrary files. Follow/comment actions verify the synthetic actor on the server, not merely in the UI. Limit synthetic payload sizes and escape user-controlled values in lab HTML and reports.

For a write with an unknown result, query authoritative lab state using its operation ID before considering a retry. Do not release or reassign the identity while its old context may still complete an action. For unsupported reconciliation, report the uncertainty and block that identity instead of resubmitting.

On restart, inspect unresolved prior runs before allowing identity/target reuse. An automatically released OS lock does not prove that descendant processes or submitted requests stopped. Preserve the interrupted manifest and unknown outcomes until owned-process/reconciliation evidence or an explicit reviewed recovery decision resolves them; do not silently expire this quarantine.

## Security completion gate

Before accepting high-risk code, link the affected threat row to concrete unit plus real-adapter/fault evidence. Cover scope rejection, lease exclusivity, secret/artifact redaction, context isolation, cancellation and unknown writes. Review locked dependencies with supported tooling and record reachable unresolved risks; no automatic forced upgrades or unreviewed deferrals.

No external load, destructive cleanup outside owned fixtures, production deployment, or global security-setting change is authorized by this document. Local smoke verification establishes only the local tested boundary.
