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
| Dense visual/numeric reporting | Validated Delta-ARI and RQ3 condition means support compact visuals | Use a 30-cell heatmap and two-panel descriptive RQ3 figure | Integrated |
| Two RQ1 runs differ | 43 ARI rows differ only at graph 2x; other result/runtime differences exist | Do not pool or assign a Python/threshold cause | Integrated |
| Conditional component bound included a singleton under a strict inequality | The edge theorem is unchanged; a singleton has `h=D=0` | Apply `D < h r` only to components with at least two nodes | Integrated |
| RQ2 narrative omitted an adverse urgency-inflation comparison | The full table already reports revised drift above legacy | Include urgency with population, vulnerability, and coordinated-campaign limitations | Integrated |
| Public-artifact wording was ambiguous | Remote `clean` is verified at `5fad10d`; `v1.0.1` remains `be95d4c` | Link the exact public commit and keep stress artifacts outside the release claim | Integrated |
| Strict 12–15 pages | Current source and fresh ZIP extraction produce 15 pages with Tectonic | Preserve LNCS margins/fonts and final science; repeat required TeX Live build | Locally verified |
| Eight-author change | User records organizer approval | Keep eight names; retain approval evidence | Group evidence pending |
| One corresponding author | Manuscript marks Thanh-Trong only and displays his full email | Match PDF, EasyChair, LTP, and proof contact | Integrated |
| EasyChair package fields | Local instructions specify ZIP, PDF, LTP, main file and engines | `main.tex` root; select XeLaTeX/BibTeX; fresh ZIP passes Tectonic; required TeX Live build remains | Locally verified |
| Accessibility | LTP requests figure alt text | Provide alt text for all three figures | Prepared |
| New-content licensing | Team chose no new CC BY grant | MIT code only; LTP contribution; preserve v1.0.1 history | Integrated |

## Remaining gates

- Original ZIP and runtime/resume confirmation for both RQ1 runs; executed v2
  notebook.
- Run the clean `xelatex -> bibtex -> xelatex -> xelatex` build on the final
  source ZIP in a TeX Live environment before upload.
- Conference confirmation of deadline time zone and alt-text delivery channel.
- Final author review of PDF, source ZIP, metadata and hand-signed LTP.
- Registration/upload receipts and any new archive/release decision.

No additional experiment is assigned by default. A rerun requires a
conclusion-affecting defect and separate approval.

The only new camera-ready experiment is the fixed RQ1 measurement/copy stress.
The expanded RQ2/RQ3 reporting and the 840-observation sensitivity analysis
come from analyses already present in the submitted paper or its accepted
artifact boundary.
