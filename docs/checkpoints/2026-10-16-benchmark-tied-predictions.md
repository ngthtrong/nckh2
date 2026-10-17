# Checkpoint: consistent benchmark predictions on tied probabilities

- Changed `products/fe/tools/compare_models.py` to sort descending probabilities stably. CSV predictions now choose the first class on ties, matching `argmax` used by summary and pairwise metrics. Confidence and top-two margin remain unchanged.
- Added one regression test covering two-way ties, multiple ties, uniform outputs, and an untied maximum. The test reproduced the old failure and passes after the fix.
- Replayed all 256 saved seed-1024 QAT probability vectors through the updated shared evaluator with mocked preprocessing/inference. The resulting CSV labels reproduce the summary confusion matrix (119/256 correct); probabilities are unchanged. Existing benchmark artifacts were not edited.
- The broader comparison test module could not complete in the bundled environment: SciPy is missing, temporary-directory writes were denied, and ExecuTorch is unavailable. The focused regression test passes.
- User may run `verify_pipeline.py --full-test --report-dir "..\reports\seed1024\verification"`. Verification and QAT comparison read the same unchanged models and write separate report directories; run them sequentially for timing measurements to avoid CPU contention.
- Next: rerun only `compare_fp32_ptq_qat.py --report-dir "..\reports\seed1024\fp32_ptq_qat"` in the user's model environment, after verification finishes. No retraining/re-export is needed for this CSV fix.
- Changes remain uncommitted; preserve unrelated model/report/diagram changes already present in the workspace.
