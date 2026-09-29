# FINAL QUALITY SUMMARY - SOURCE FINAL v5.0.0

## Audit structure

### Layer 1 - Source basis: 10 rounds
Results deliberately preserve boundaries/adaptations instead of forcing all checks into an unconditional PASS.

{'PASS_WITH_BOUNDARY': 4, 'PASS': 2, 'PASS_AFTER_CHANGE': 2, 'EXCLUDED_FROM_LR': 1, 'ADAPTATION_DISCLOSED': 1}

### Layer 2 - Dataset integrity: 10 rounds
{'PASS': 10}

### Layer 3 - Final quality gate: 10 rounds
{'PASS': 10}

## Final dataset

- Train file: `data/urgency_training_SOURCE_FINAL.csv`
- Rows: 32
- Unique feature profiles: 32
- Coverage: complete 2^5 Boolean state space
- Duplicate profiles: 0
- Random row generation: no
- LLM row generation: no
- Real-patient data: no
- Expert labels: no
- Clinical ground truth: no

## Source-aligned features

1. unresponsive
2. respiratory_distress_or_cyanosis
3. heavy_bleeding
4. active_convulsions
5. high_risk_trauma

`cannot_move` remains documented context but was removed from the LR train features after source audit.

## Evaluation interpretation

The 10-round unseen-positive-profile sanity test has no train/test profile overlap. It is a technical surrogate-generalization check.
The direct rule remains an exact baseline for the reduced label definition; Logistic Regression should not be claimed superior to that rule.

## Required report wording

Call the table a **deterministic protocol-state synthetic reference table** and the target a **guideline-derived mapped-high-acuity surrogate label**.
Call E_i a **guideline-derived urgency evidence score**.

Do not claim:
- WHO created or validated this 32-row table;
- expert-annotated clinical ground truth;
- full WHO/IITT triage implementation;
- clinical accuracy or field effectiveness;
- E_i as mortality/dispatch probability.
