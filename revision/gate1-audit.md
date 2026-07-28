# Gate 1 method/data freeze audit

**Verdict:** PASS and locked  
**Lock:** `revision/gate1-lock.json`  
**Accepted run:** `20260728T181154Z-1651b35ac599-225cd4b0-gate1-data-freeze`

Gate 1 freezes the theorem/code boundary, the priority aggregation API, and
the synthetic generator/schema/data bundle before downstream calibration.
The accepted candidate run succeeded with exit code zero, its sealed manifest
passes exact file-set and checksum validation, and its data-quality acceptance
uses no clustering or preferred-method performance metric.

## Evidence

- Full suite: 96 tests and 41 subtests passed; zero failures.
- Product/additive bounds: full parameter-domain classification, strict
  threshold equality, non-finite/invalid parameter rejection, near-equality
  and subnormal numerical boundaries all pass.
- Priority: exact duplicates are invariant, inconsistent confidence fails
  closed, `C=0` contributes no priority evidence, and the registered
  single-near-duplicate drift contract passes.
- Data: all 80 registered seeds regenerate byte-identically; 30,229 reports
  pass every method-agnostic quality gate; all 36 validator mutation probes
  are rejected.
- Distribution audit: overall, split, family, and split-family coverage is
  complete; no report/incident identifiers or method-performance endpoints
  are emitted.
- Reproducibility: `requirements.lock` is the sole canonical dependency lock;
  the clean environment imports all experiment modules. The candidate runner
  captures Git state, environment, command, inputs, logs, outputs, timestamps,
  and checksums without overwriting an earlier run.

Three independent audit scopes returned PASS: method/priority/protocol/
environment/artifacts, generator/schema/data, and the distribution report.
The exact hashes and accepted manifest path are machine-readable in the lock.

## Preserved adverse history

The two earlier candidates remain recorded in `revision/rejected-runs.json`.
The first was rejected after independent audit exposed leakage and atomicity
failures. The second was interrupted before sealing after a validator mutation
escaped. Neither is eligible for promotion; neither was deleted.

## Boundary after this gate

Development and calibration work may now use only the frozen data and method
contracts. Test seed release remains blocked until Gate 2 records the exact
protocol hash. Any change matching a `reopen_conditions` entry in the lock
invalidates this gate and requires a new method-agnostic freeze.
