# Revision change ledger

This ledger maps the Reject-and-Resubmit concerns to implemented changes,
locked evidence, manuscript disposition, and unresolved external inputs.
Historical `demo/results` tables and Loop-17 claims are not evidence for the
revision.

| Work item | Change | Primary evidence | Manuscript effect | Status |
|---|---|---|---|---|
| R0 / Gate 0 | Locked scope, theorem, priority, test, endpoint, and source-of-truth decisions | `revision/decision-log.md`, `revision/source-snapshot.json` | Synthetic methodological scope | Complete |
| A1–A2 / MC1 | Complete product/additive domains; strict threshold; conditional component corollary | `revision/math-spec.md`, `demo/pipeline/weighting.py`, theorem tests | Replaced theorem and removed old violation figure/counts | Complete |
| B1 / MC2 | Disjoint 20/20/40 seeds, two tracks, equal budgets and multiplicity policy | `demo/protocol/*.json` | Replaced shared-default design | Complete |
| C1–C2 / MC4 | Latent incident truth, consistent confidence gating, exact/near duplicate handling, capped strongest evidence | `revision/priority-contract.md`, `demo/pipeline/priority.py`, tests | Replaced legacy priority equations; added limitations | Complete |
| D1–D2 / MC3 | Generator/schema v4 and method-agnostic freeze over 80 datasets | `revision/data-spec.md`, `revision/gate1-lock.json` | Replaced seed-42 benchmark | Complete |
| D3–D4 / MC3 | Rights/annotation/evaluation protocol for real reports | `revision/real-data-protocol.md` | Explicitly states no real-data validation | Protocol complete; collection external-blocked |
| C5 / MC4 | Expert elicitation and blinded vignette protocol | `revision/expert-validation-protocol.md` | Score/caps/weights called illustrative | Protocol complete; panel external-blocked |
| E1 / MC6–MC7 | Strong baseline registry and endpoint contract | `demo/protocol/baselines.json`, `demo/protocol/metric_contract.json` | Adds ST-DBSCAN/spatial/convex comparators and burden endpoints | Complete |
| F1–F2 / MC8 | Exact dependency lock, isolated runner, manifests, checksums, environment capture | `pyproject.toml`, `requirements.lock`, `demo/experiments/artifacts.py` | Reproducibility section rewritten | Complete |
| Gate 1 | Locked method, generator, schema, 80 datasets, and environment | `revision/gate1-lock.json`, `revision/gate1-audit.md` | Defines all downstream inputs | Locked |
| B2/E2/E3/C3/C4/F4 | Calibration, baselines, factorial, burden, robustness, dispatch, runtime | Accepted Exp15–Exp22 run manifests in `revision/gate2-audit.md` | Supplies pre-test evidence and selections | Complete |
| Gate 2 | Promoted 12 selections, retained 8 no-feasible exclusions, released test once | `revision/gate2-lock.json`, `demo/protocol/selected_configs.json` | Establishes fair test protocol | Locked |
| X0 | One complete held-out run; 480 selected rows, 320 exclusion rows | accepted Exp23 manifest | Replaces all historical headline results | Complete, no rerun |
| Gate 3 | Independent result/inference/selector recomputation | `revision/gate3-lock.json`, `revision/gate3-audit.md` | Permits publication promotion | Locked |
| G0 | Compact result, full gzip archive, 448 selectors, 9,451 numeric claims/macros | `revision/result-lock.json`, `loop/revision/traceability.md` | Every empirical paper value is generated | Locked |
| G1 | Rewrote title, abstract, method, design, results, threats, conclusion; removed all legacy figures | `paper/main.tex`, `paper/generated/revision_results.tex` | Product similarity; adverse findings in main text | Complete |
| G2 | Point-by-point response and this ledger | `revision/response-to-reviewer.md` | 8/8 MC plus minor concerns addressed/dispositioned | Complete |
| F3 | One-command locked-output verification, tests, XeLaTeX/BibTeX build, and persisted clean-room transcript/report | `reproduce.sh`, verifier, companion package, `revision/clean-room-full.log`, `revision/clean-room-report.md` | Correct reviewer instructions | Complete; full profile passed |
| G3 / Gate 4 | Final source/claim/PDF/clean-room checksum audit | `revision/final-audit.md`, `revision/submission-checksums.json` | Local synthetic-methodological submission lock | Complete; Gate 4 locked locally |

## Scientific outcomes retained

- Product Louvain has higher calibrated ARI than additive on both synthetic
  test tracks.
- Product is not uniformly better: Leiden ties it; additive has smaller
  destination diameter; ST-DBSCAN improves split/noise outcomes; product
  retains substantial false-destination/review burden.
- Factorial interactions and 80 density-unmatched cells remain visible.
- Exact duplicates are invariant under the revised priority estimator.
- Coordinated high-confidence reports make revised priority drift worse than
  legacy.
- Revised priority does not establish independent dispatch benefit; simple
  nearest-first policies outperform it on harm/deadline endpoints in the shown
  scenarios.
- Real-data and expert validation remain unresolved rather than being inferred
  from synthetic evidence.

## External submission actions

The authors must still supply or approve:

1. public repository/archive URL and DOI;
2. final clean commit/tag and release authority;
3. venue/page-limit policy;
4. ORCID, author order/contact/affiliations, and authorship consent;
5. funding and competing-interest declarations;
6. any future real-data rights/ethics record and expert-panel participation.

These actions do not authorize reopening the held-out protocol or selecting a
different X0 result.
