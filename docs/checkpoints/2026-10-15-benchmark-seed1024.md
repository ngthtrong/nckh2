# Checkpoint: benchmark image seed 1024

## Current state

- The shared image split CSV has 1,702 records: 1,189 train, 257 validation, 256 test. Its SHA-256 is `f7b52cd25411d4d1df2f7f80745a2cf430819773854345798cf7e093e3bcba45`.
- The cleaned seed-1024 records match all split identities; validation error files contain 64 and 6 valid validation rows. The checkpoint does not store the CSV hash or complete sample assignments, so this confirms consistency with the shared split, not the exact original training manifest.
- User's seed-1024 PTH/ONNX/PTE full-test results are selected in `report/config/benchmark-sources.json`: 256 test images, Accuracy 75.78%, macro-F1 74.26%, and 100% top-1 agreement between formats. The confusion matrix reproduces the seed-1024 test CSV.
- Quantization, structured pruning, and phone measurements still use archived seed-42 evidence. Their source paths and labels are explicit. The report suppresses CPU/mobile parity interpretation across seeds.
- The benchmark package carries a fingerprint of the fixed split CSV. Its sample IDs, labels, and image payload bytes are unchanged.
- Re-exported 14 report tables and 12 figures; rebuilt `report/build/content/content.pdf` (106 pages, 80 pages from introduction through conclusion). A visual check of source/runtime/mobile/conclusion pages found no layout issue.

## Verification

- `report/scripts/test_export_results.py`: 2 tests pass.
- `products/be/test_benchmark_package.py`: passes; backend suite previously passed 69 tests.
- `git diff --check`: passes.
- `report/scripts/check_report.py` confirms source/hash checks, 12 figures, and 80 body pages, then stops because `pdftotext` is unavailable on PATH. Tectonic completed successfully with existing underfull-box, font-path, and BibTeX warnings.
- Archived seed-42 PTQ/QAT summaries still differ from prediction CSV in two metrics; the report exposes both values and the discrepancy count.

## Next runs

Use `docs/benchmark-seed1024.md` for commands. Remaining seed-1024 work, if needed, is PTQ/QAT, structured pruning, and a rebuilt/reinstalled APK followed by phone runs. Update only the relevant entries in `report/config/benchmark-sources.json`, then regenerate tables, figures, and PDF.
