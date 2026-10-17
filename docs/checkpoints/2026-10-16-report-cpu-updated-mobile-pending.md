# Report update: seed-1024 CPU complete, mobile files pending

## Completed

- Selected seed-1024 FP32, PTQ/QAT, structured pruning (`prunning_st` directory), and full-test verification in `report/config/benchmark-sources.json`.
- Independently checked every CPU comparison CSV: 256 expected test paths/labels, matching config/split/model hashes, confusion matrices, Accuracy and macro-F1. QAT CSV now agrees with summary after the tie-handling fix and rerun.
- FP32 Accuracy/F1: 75.78%/74.26%; PTQ: 66.80%/64.36%; QAT: 46.48%/42.91%; structured pruning: 80.08%/78.26%. Pruning has 4 critical errors versus 3 for baseline, and median latency improves only for PTH in this paired CPU run.
- Verification covers 256 images, `pass_local`, 5 passed checks and 0 failed checks. The exporter now checks full-test scope, model hashes and config/split hashes against the selected FP32 evidence.
- Updated generated tables, confidence/compression figures, result prose, conclusion, research-result forms, implementation description and source register. The selected CPU artifacts have 0 summary/CSV discrepancies.
- Three report integration tests pass, including rejection of subset verification and a different checkpoint. `git diff --check` passed.

## Waiting on user

User explicitly chose to wait for complete mobile files instead of publishing partial summaries. Keep the selected historical seed-42 mobile source and its explicit label until replacement files are available; do not claim the complete report has switched to seed 1024.

Three new files contain exactly 20,000 decoded characters and invalid/truncated JSON:

- `products/fe/reports/seed1024/mobile/redminote11/onxx.txt`
- `products/fe/reports/seed1024/mobile/redminote11/pte.txt`
- `products/fe/reports/seed1024/mobile/redminote13/pte.txt`

`redminote13/onxx.txt` is complete (256 predictions). Its test IDs, labels and nearest-rank latency summary match; CPU top-1 agreement is 242/256. Do not infer complete PTE or cross-runtime agreement from matching aggregate metrics.

Next: validate all four full mobile files; adapt the source selection/table/plot to both device labels, audit each pair separately, update mobile prose and metadata limits, regenerate and visually verify the final report. Raw mobile JSON currently lacks APK/model hashes, OS/SoC and measurement timestamp; device names come from user-provided directory labels.

## Build limitation

The intermediate report compiles with Tectonic (105 PDF pages, no unresolved `??` markers). Visually reviewed the revised research-result forms, quantization/pruning tables and conclusion; shortened the Vietnamese summary to keep its signature on the same page. Existing font-path/underfull-box/BibTeX warnings remain. The complete `check_report.py` gate still needs `pdftotext` on PATH; no claim that the full release gate passed. No raw experiment/model/database files were changed by this report update.
