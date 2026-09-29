# Urgency E_i - SOURCE FINAL v5.0.0

This is the final source-grounded package for the structured urgency Logistic Regression.

## Use these files

### Training dataset
`data/urgency_training_SOURCE_FINAL.csv`

- 32 rows
- 32 unique feature profiles
- complete 2^5 Boolean state space
- no duplicate feature profiles
- no free-form LLM-generated cases

### Master/audit dataset
`data/urgency_reference_master_SOURCE_FINAL.csv`

Includes:
- `label_basis`
- `source_ids`
- `active_source_mapped_signs`
- `feature_semantics`
- `generation_method`
- `builder_sha256`
- explicit non-LLM and non-clinical-ground-truth flags

### Train script
`scripts/train_urgency_logistic.py`

### Deterministic dataset builder
`scripts/build_source_aligned_dataset.py`

### Final model artifact
`model/urgency_logistic_SOURCE_FINAL.json`

## Three required 10-round audit layers

1. `audits/01_source_basis_audit_10_rounds.csv`
2. `audits/02_dataset_integrity_audit_10_rounds.csv`
3. `audits/05_final_quality_gate_10_rounds.csv`

Extra model sanity:
- `audits/03_model_sanity_10_rounds_unique_profiles.csv`
- `audits/04_rule_baseline_comparison_32_profiles.csv`

## Final reports

- `reports/DATASET_METHOD_REPORT_FINAL.docx`
- `reports/DATASET_METHOD_REPORT_FINAL.pdf`
- `reports/SOURCE_AND_DATASET_AUDIT_FINAL.docx`
- `reports/SOURCE_AND_DATASET_AUDIT_FINAL.pdf`
- `reports/FINAL_QUALITY_SUMMARY.md`
- `reports/CHANGELOG_v4_to_v5.md`

## Source-aligned LR features

- unresponsive
- respiratory_distress_or_cyanosis
- heavy_bleeding
- active_convulsions
- high_risk_trauma

`cannot_move` and `injured_count` remain app/report context but are not v5 LR train features.

## Scientific boundary

This is a deterministic protocol-state synthetic reference table.
It is not a WHO-provided dataset, not expert-annotated clinical ground truth,
and not a full WHO/IITT triage implementation.

E_i is a guideline-derived mapped-high-acuity evidence score, not a calibrated clinical probability.
