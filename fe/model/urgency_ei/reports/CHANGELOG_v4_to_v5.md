# Changelog: v4 -> SOURCE FINAL v5

The dataset was changed after stricter source audit.

1. **Removed `cannot_move` from Logistic Regression features.**
   Mobility remains valid contextual data (MC-IITT/START/SALT), but the binary v5 target is specifically the presence of selected WHO-IITT RED signs.
2. **Renamed `seizure` -> `active_convulsions`.**
   This matches the primary source term and avoids treating seizure history as an active high-acuity sign.
3. **Renamed `major_trauma` -> `high_risk_trauma`.**
   This matches WHO-IITT wording and is linked to the WHO reference card.
4. **Renamed `respiratory_distress` -> `respiratory_distress_or_cyanosis`.**
   This preserves the adult IITT source criterion more faithfully.
5. **Reduced train state space from 64 (2^6) to 32 (2^5).**
   All 32 profiles are unique and exhaustively enumerated.
6. **Removed row-level balancing weights from the CSV.**
   The train script uses `class_weight='balanced'`; no duplicate rows are introduced.
7. **Master CSV now contains explicit `label_basis`, `source_ids`, provenance, builder SHA-256 and non-LLM flags.**
8. **Added three independent audit layers plus direct-rule baseline comparison.**

Scientific boundary: v5 is a deterministic protocol-state reference table and a learned surrogate of a reduced mapping. It is not a clinical dataset and does not implement full WHO triage.
