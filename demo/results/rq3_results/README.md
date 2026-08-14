# RQ3 paired-inference artifacts

`rq3_dispatch_test.csv` and the original `rq3_paired_comparisons.csv` retain
the notebook's diagnostic unit of 40 seeds × 3 resource scenarios (120 paired
rows per comparison). They are preserved for audit and are not the primary
inferential result in the long-paper revision.

The primary revision uses `rq3_dispatch_test_seed.csv` and
`rq3_paired_comparisons_seed.csv`. The three resource scenarios are averaged
within each seed, giving 40 paired seed observations. The script
`recompute_seed_level.py` applies the same direction-oriented Wilcoxon,
5,000-resample bootstrap, and 14-endpoint Holm family to those seed-level
observations. `rq3_seed_level_reanalysis_provenance.json` records input/output
hashes and the runtime used for the regeneration.
