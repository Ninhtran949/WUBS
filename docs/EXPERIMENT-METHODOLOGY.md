# Experiment methodology

Status: measurement contract for F07-F11; no benchmark has been run. The reporting rules below are project policy, not claims of scientific significance or hardware capacity.

## Definition before execution

Each experiment declares its question, one engine, target/build/fixture version, ordered scenarios, account cohort, workload model, finite budgets, timing profile, seed, warm-up, measurement window, repetitions, failure thresholds and artifact policy. Record the effective configuration and any deviation rather than silently adjusting it during the run.

Use separate UI and HTTP experiments. Browser context concurrency, HTTP virtual users, request arrival rate, completed RPS and scenario throughput are different quantities. A ramp in user count is not an arrival-rate generator. The initial controller and Locust workloads are closed-loop; an open-loop generator is a separately specified capability, not a relabeling of a sleep interval. See the [k6 model explanation](https://grafana.com/docs/k6/latest/using-k6/scenarios/concepts/open-vs-closed/) and [Locust wait-time limitations](https://docs.locust.io/en/stable/writing-a-locustfile.html#wait-time-attribute).

Record software revision or source fingerprint, dirty state when available, Python/uv/library/browser versions, OS, CPU/RAM, power/network profile, workload definition, fixture reset ID, run timestamps, and resource probe availability. Missing Git metadata is recorded explicitly. Do not publish hostname/user identity or secrets as environment provenance.

## Timing and sampling

| Observation | Definition |
| --- | --- |
| Queue wait | Admission/enqueue to worker start, with monotonic timestamps. |
| Scenario latency | Start of scenario execution to its terminal outcome, with think time reported separately. Cleanup is a separate duration. |
| Action latency | Declared action boundary to its observable assertion, identified by action name. |
| Navigation timing | Browser-reported navigation metrics and availability, separate from controller wall time. |
| Request latency | One observed HTTP request boundary, tagged by engine, route template and outcome. |
| Throughput | Completed cases or requests divided by the explicitly stated measurement-window seconds; never users divided by time. |
| Failure/timeout rates | Failure count and timeout subset count with their named denominator; timeouts are counted once in total failures. |
| Resource/context/worker gauges | Timestamped samples for generator and owned browser/load processes, context count, active workers, queue depth and cancellations, with sampling interval and coverage. |

Use monotonic clocks for elapsed durations and timezone-aware UTC for persisted timestamps. Store unit-labeled raw observations before deriving aggregates. Emit structured sanitized events to `system_test.log`; aggregate CSV/histogram summaries from another engine must not be mistaken for individual request samples.

Report `started`, `completed`, `failed`, `blocked`, `cancelled`, `not_run`, and retries separately. For cases, show FAILED / started cases and COMPLETED / started cases together; disclose blocked/cancelled counts. For HTTP, show failed / completed requests and the independently tracked started/unfinished counts. A zero denominator yields unavailable, not zero percent. A partial run cannot appear successful because cancelled work disappeared from a denominator.

Keep outcome groups separate. Primary successful-case latency excludes failures/timeouts, with excluded counts shown; report failed-attempt observations separately. Timeouts are censored observations, not successful responses equal to the timeout setting. Always state whether a duration includes queue time, think time, retries, or cleanup.

## Randomness and warm state

- Derive a local RNG stream from the root seed plus stable scenario ID, planned case index and attempt index. Do not use Python's process-randomized `hash()` or shared global random draws whose order depends on worker completion.
- Record effective delays and workload assignment. A repeatable seed reproduces input/timing choices; it does not promise identical OS scheduling, backend state, or measured latency.
- Declare browser-process cold/warm state, context freshness, authentication reuse and target/cache state independently. Restoring authentication into a fresh context is not evidence of a warm HTTP cache. Do not merge cold-start and warm-session observations.
- Reset only the experiment's synthetic namespace. Record initial state and warm-up traffic; exclude the declared warm-up window consistently from primary comparisons.

## Percentiles and interpretation

For each engine/scenario/outcome/window, preserve sample count and the percentile method. Initial project policy uses inclusive linear interpolation on retained observations. Never average percentiles or reconstruct a request distribution from per-task averages.

Suppress tail percentiles below the following sample counts and retain an explicit insufficient-samples reason:

| Statistic | Minimum observations |
| --- | --- |
| p50 | 20 |
| p90 | 100 |
| p95 | 200 |
| p99 | 1,000 |

These are conservative SE/SA display heuristics (roughly ten expected observations beyond the quantile), not a confidence guarantee. Correlation, autocorrelation, censoring and run-to-run variation still matter. Preserve raw data even when a statistic is suppressed. A ten-case smoke can verify the reporting path while legitimately displaying no percentile.

For performance claims, predeclare at least three independent repetitions, preserve every run, report variation, and document deviations. Do not select only successful repetitions. A noisy, incomplete or generator-saturated run needs a qualification; a single smoke has no performance conclusion.

## Capacity and compatible comparison

Calibrate on the actual host before raising concurrency. Record active processes, memory and CPU saturation, background load and missing probes; no fixed context-to-RAM formula proves capacity. If the generator becomes the bottleneck, describe its observed limit rather than attributing all latency to the target.

Comparison requires matching engine/model, scenario and fixture versions, cohort definition, target/build intent, warm state, timing, limits and measurement windows. Hardware/software/network differences must be identified and either rejected for automatic comparison or explicitly marked exploratory. Never label UI concurrency versus HTTP users as an equal-load comparison.

Keep raw data immutable and regenerate summaries with the schema/method version recorded. Clearly separate browser-side observations, generator measurements and independently instrumented server evidence. Do not infer server latency or causation from client timings alone. Linux/Docker distributed guidance is future operational documentation; it is not evidence of Windows distributed-load support.
