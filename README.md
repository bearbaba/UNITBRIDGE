# UNITBRIDGE — Intelligent sensor interoperability

Two Intelligent Contracts bridge heterogeneous temperature telemetry without a document compiler or bilateral approval workflow.

- **UnitBridge** registers immutable source profiles. GenLayer leader and independent validators classify a single-line sensor description as absolute AIR, SURFACE, LIQUID or REVIEW. Explicit C/F/K units are not inferred. Exact affine conversion produces integer ticks (1 tick = 1/9000 K) and uncertainty intervals.
- **SensorFusion** pins the actual registry contract. A round selects 2–5 active source IDs, distinct wallet owners, the same declared site and semantic kind, and a strict majority quorum. Each owner submits a reading once. When all submit, deterministic interval sweep identifies the unique maximum-support interval, reports excluded sources, or returns CONFLICT / REVIEW without a fabricated aggregate. No signer approves another's reading.

## Live walkthrough
See [Studio steps](docs/walkthrough.md) and [evidence](docs/evidence.md). All inputs fit single-line Studio fields; integers represent thousandths of the declared unit. No frontend, API keys, payments or mainnet.

## Trust and limits
Profiles, site, time-window labels, readings and uncertainties are wallet-attested metadata; no physical sensor authentication, synchronization, calibration guarantee or independent identity proof. Distinct addresses are not proof of distinct people. AI consensus classifies labels, not physical truth, and can be wrong. The caller selects the sources; no automatic discovery. All selected sources must report, so absent sources can stall a round. Source IDs are first-come, immutable; select known IDs and owners. Only absolute temperature in C/F/K, intervals within 0–500 K and uncertainty at most 10 K. The result is an agreement interval, not a calibrated estimate or safety-critical recommendation. No timestamps or external data.

## Tests
CI uses genvm-linter 0.11.1rc2, genlayer-test 0.30.0 and pytest. Direct-mode tests mock AI outputs and registry reads; real Studio deployment and consensus are separate evidence.
