# ISDS-2026 camera-ready evidence tracker

Submitted baseline: `v1.0.1` (`be95d4c`). Implementation baseline: branch
`clean` at `edefb9c`. Stated deadline: 16 September 2026; exact time zone is
still pending. This internal tracker evaluates evidence and fit with the study;
it is not part of the manuscript narrative.

| Observation or requirement | Evidence and fit | Decision | Status |
|---|---|---|---|
| Product/Additive superiority is not established | Adjusted RQ1 comparisons remain inconclusive | Present localization as a checkable property, not superiority | Integrated |
| Synthetic realism must be bounded | Reports, attacks, labels and outcomes are simulated; upstream lineage is incomplete | Retain construction table and field-validity limits | Integrated |
| Measurement/copy stress should be exposed | Two fully audited fixed-protocol runs exist | Use primary values; report v2 as unpooled replication | Integrated |
| RQ1 does not establish dispatch benefit | RQ3 is a separate Candidate-4.1 suite | Keep clustering and dispatch conclusions separate | Integrated |
| Exact-copy score invariance can be overgeneralized | It requires fixed grouping and inputs | Do not extend it to clustering or the pipeline | Integrated |
| Formula notation needed completion | Four main equation groups checked against implemented rules | Define variables, units, ranges and continuous numbering | Integrated |
| Dense prose duplicated numeric tables | Validated Delta-ARI cells support a compact visual | Use 30-cell vector heatmap; remove redundant figures/table | Integrated |
| Two RQ1 runs differ | 43 ARI rows differ only at graph 2x; other result/runtime differences exist | Do not pool or assign a Python/threshold cause | Integrated |
| Strict 12–15 pages | Dockerized Tectonic produces 15 pages | Preserve LNCS margins/fonts and final science | Verified |
| Eight-author change | User records organizer approval | Keep eight names; retain approval evidence | Group evidence pending |
| One corresponding author | Manuscript marks Thanh-Trong only | Match PDF, EasyChair and LTP | Integrated |
| EasyChair package fields | Local instructions specify ZIP, PDF, LTP, main file and engines | `main.tex` root; select XeLaTeX/BibTeX; clean ZIP build passed | Verified |
| Accessibility | LTP requests figure alt text | Provide alt text for pipeline and heatmap | Prepared |
| New-content licensing | Team chose no new CC BY grant | MIT code only; LTP contribution; preserve v1.0.1 history | Integrated |

## Remaining gates

- Original ZIP and runtime/resume confirmation for both RQ1 runs; executed v2
  notebook.
- Repeat the clean `xelatex -> bibtex -> xelatex -> xelatex` build only if an
  approved final edit changes the source ZIP.
- Conference confirmation of deadline time zone and alt-text delivery channel.
- Final author review of PDF, source ZIP, metadata and hand-signed LTP.
- Registration/upload receipts and any new archive/release decision.

No additional experiment is assigned by default. A rerun requires a
conclusion-affecting defect and separate approval.
