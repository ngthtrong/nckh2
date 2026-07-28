# Real flood-report access and annotation protocol

**Task:** D3  
**Local status:** protocol complete  
**Access status:** external-blocked — no source, permission, or annotators are
available in the repository.

This document defines the minimum evidence needed for D4. It does not authorize
collection, infer consent, or turn public-looking posts into research data.

## Required source and rights record

Before any data are copied, the authors must record:

- source owner and a named data steward;
- lawful basis, license/terms, research purpose, retention period, and allowed
  publication level;
- whether coordinates, timestamps, images, text, names, phone numbers, account
  handles, or health/vulnerability information are present;
- institutional/ethics review outcome and consent requirements;
- permitted de-identification, linkage, model use, and artifact release;
- deletion/contact process and access-control owner.

If any item is unresolved, raw data are not committed and D4 remains blocked.

## Minimum analytical content

The intended unit is an independently annotated physical rescue incident.
The minimum usable sample is set before model execution using expected
precision/CI and incident/family coverage, not a convenient number observed
afterward. The sample must include:

- geolocated, time-resolved reports;
- at least two reports for a meaningful subset of incidents;
- both singleton/noise reports and genuine repeated reports;
- enough spatial/temporal overlap to test split and merge behavior;
- documented coverage across source, region, and time.

Exact coordinates/times are retained only in the protected analysis
environment. Released derivatives use the coarsest precision compatible with
the approved analysis.

## Data dictionary

The protected source table records a pseudonymous report key, source key,
timestamp/timezone, coordinates/precision, observable `F/E/N/V` when actually
available, evidence provenance, and redaction status. Missing values stay
missing; annotators do not invent synthetic replacements.

The annotation table is separate and contains:

- incident assignment or `unresolvable/noise`;
- duplicate relation (`same`, `near`, `independent`, `uncertain`);
- confidence in the assignment;
- observable evidence used;
- adjudication outcome;
- optional incident-level demand/vulnerability ranges when evidence supports
  them, never fabricated point estimates.

Direct personal identifiers, free text, images, phone/payment details, and
precise home locations are excluded from repository artifacts.

## Annotation procedure

1. Freeze the guide and a small training set before held-out annotation.
2. At least two annotators label the same blinded overlap set independently.
3. Annotators do not see proposed-method clusters, scores, or parameters.
4. Measure pairwise incident-link agreement and report an agreement statistic
   suited to clustering/linkage, with raw agreement and uncertainty.
5. Adjudicate disagreements using a third reviewer or documented consensus.
6. Preserve `uncertain` rather than forcing a label.
7. Freeze a development/held-out split by incident, region, or time before
   model tuning.

## Held-out evaluation

The real-data adapter maps only observable approved fields into the frozen
Gate-1 API. No tuning occurs on held-out incidents. Predefined outputs are:

- ARI or pairwise linkage agreement on resolvable annotations;
- incident split/merge loss;
- noise rejection/absorption;
- false operational destinations and review burden;
- geographic spread and connectivity;
- domain-shift profile against synthetic data;
- annotation agreement and an error table including uncertainty.

Priority/dispatch claims require independently observed outcomes or expert
policy validation. Incident labels alone do not validate the priority score.
All results, including inconclusive or adverse transfer, are retained.

## Privacy-preserving artifact

Only aggregate tables, de-identified examples explicitly approved for release,
code, data dictionaries, annotation instructions, checksums, and access
metadata may enter the repository. A protected manifest may prove the held-out
source state without publishing raw records. Small cells are suppressed
according to the data steward's policy.

## Completion gate

D3 access passes only when rights and stewardship are documented and the
annotation process is staffed. D4 passes only after a frozen held-out run with
coverage justification, agreement, all predefined metrics, and failure cases.
Until then, the manuscript fallback is “synthetic methodological study; real
incident-level validation remains unresolved.”
