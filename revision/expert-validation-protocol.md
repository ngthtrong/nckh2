# Expert validation protocol for priority policy

**Task:** C5  
**Status:** protocol complete; recruitment, elicitation, endorsement, and
signed/anonymous evidence are **external-blocked**  
**Scope:** priority semantics, policy parameters, and dispatch trade-offs  
**Minimum-study fallback:** if no panel is obtained, every weight/cap remains an
illustrative policy knob and the manuscript states that expert validation is
absent.

## 1. Purpose and non-purpose

The study asks whether practitioners find the meanings, limits, and trade-offs
in `revision/priority-contract.md` operationally coherent. It does not ask
experts to certify deployment readiness, estimate algorithmic accuracy from
memory, endorse the paper, or convert a small convenience panel into empirical
evidence about all flood-response organizations.

Primary questions are:

1. Are `E/F/N/V/C` interpreted and gated appropriately?
2. Is “reported demand evidence” an acceptable name when unique people cannot
   be identified?
3. Are exact/near-duplicate handling and marginal-influence limits safe enough
   for an operator queue?
4. Which ranges for `omega_E/F/N`, `mu`, `v_scale`, `N_cap`, `V_cap`, and human
   review thresholds are defensible?
5. Which outcome endpoints and equity–efficiency trade-offs must be reported
   together?
6. What failure requires human verification or prevents automatic dispatch?

## 2. Panel, independence, and ethics gate

Eligible participants have current or recent experience in at least one of:

- flood rescue/incident command;
- humanitarian logistics or emergency dispatch;
- field triage/community disaster response;
- operational risk, safeguarding, or data verification in emergency response.

Record role family, years of relevant experience, geographic context, and
whether the participant has a relationship with the authors. Do not publish
names, employers, direct contact details, signatures, or free-text that could
identify a participant unless explicit written permission covers that use.

Acceptance requires either:

- at least two experts completing the elicitation independently before seeing
  one another's answers; or
- one facilitated workshop with at least two eligible participants, a
  contemporaneous minute-taker, individual pre-votes, and an archived
  disagreement record.

Before recruitment, the authors/institution must decide whether ethics review,
consent documentation, honoraria disclosure, data-retention approval, or a
formal exemption is required. This repository cannot make that determination.
No interview starts until that gate and the participant information/consent
text are approved.

## 3. Materials frozen before elicitation

Provide each participant the same versioned packet:

1. one-page synthetic-only scope and limitations;
2. plain-language field definitions and the revised formula;
3. score ranges and all policy caps;
4. exact- and near-duplicate definitions;
5. six to ten synthetic, non-identifying incident/report vignettes;
6. side-by-side priority rankings under varied policy settings;
7. dispatch outcome cards showing mean response, deadline misses, maximum and
   CVaR response, unique-population coverage, and review burden together;
8. the structured response form and terminology glossary.

At minimum, vignettes cover: exact duplicates; near duplicates; low-confidence
inflation separately for `N`, `V`, `F`, and `E`; missing image/corroboration;
overlapping genuine reports; and a coordinated high-confidence campaign. At
least one vignette must show an unfavorable equity–efficiency trade-off and one
must produce no clear preferred ordering.

Freeze the packet checksum, software/config version, scenario values, question
order, recruitment criteria, and analysis template before the first response.
Do not replace a vignette because experts disagree with the implemented
policy.

## 4. Elicitation procedure

### Stage A — independent semantic review

Participants first answer independently:

- whether each field definition is clear;
- whether it is report evidence or incident truth;
- whether confidence should gate it;
- whether the chosen aggregation is acceptable, unsafe, or uncertain;
- what additional provenance/operator context is needed.

Use a five-point acceptability scale plus “insufficient information,” followed
by optional rationale. Ask explicitly whether any wording implies unique
population truth or misinformation detection without evidence.

### Stage B — parameter ranges

Elicit ranges before asking for a single setting:

- allocate 100 points across `omega_E`, `omega_F`, and `omega_N`;
- give minimum, preferred, and maximum acceptable `mu`;
- review `N_cap`, `V_cap`, `v_scale`, and the 10% single-near-duplicate drift
  threshold;
- define hard-stop and mandatory-human-review conditions.

A minimal AHP pairwise comparison may be used only as a consistency aid:
`E vs F`, `E vs N`, and `F vs N`. Report the scale, normalization method, and
consistency ratio. Do not discard an inconsistent response silently; ask once
for clarification and retain the original plus revised answer.

### Stage C — blinded vignette ranking

Randomize the order of synthetic clusters and hide estimator names. Ask for:

- rescue-order ties allowed;
- confidence in the ranking;
- cases that require manual verification;
- the most harmful plausible misranking and why.

Compare expert ordering with legacy and revised policy ordering only after
independent responses are locked. Agreement is descriptive; a small panel does
not become a tuning test set.

### Stage D — disagreement round

Return an anonymized summary of medians, ranges, and rationales. A second Delphi
round or facilitated discussion may clarify misunderstandings, but preserve
all first-round responses. Consensus is not required. Record whether movement
came from corrected terminology, new operational information, or social
agreement.

## 5. Parameter-to-rationale trace

Complete this table from actual responses; blank cells are not permission to
invent a rationale.

| Policy item | Current illustrative value | Expert question | Required evidence artifact |
|---|---:|---|---|
| `omega_E` | `0.34` | relative role of urgency | individual allocations, range, rationale |
| `omega_F` | `0.33` | relative role of flood severity | individual allocations, range, rationale |
| `omega_N` | `0.33` | role of reported demand evidence | individual allocations, range, rationale |
| `mu` | `2.0` | maximum vulnerability amplification | min/preferred/max and reversal concerns |
| `v_scale` | `10` | rate of vulnerability saturation | vignette sensitivity and rationale |
| `N_ref/N_cap` | `500` | operational reference and claim cap | region/capacity assumptions and acceptable range |
| `V_cap` | `50` | per-evidence-unit vulnerability cap | definition/unit and acceptable range |
| exact fingerprint | fixed allow-list | fields safe for idempotent collapse | accept/reject/missing fields |
| near envelope | `100 m`, `10 min`, field tolerances | false-merge vs duplicate-inflation trade-off | acceptable ranges and boundary cases |
| near drift ceiling | `10%` of score range | acceptable single-copy impact | accept/reject and alternative threshold |
| `C=0` rule | zero priority contribution | treatment of untrusted reports | accept/reject plus human-review rule |
| dispatch outcomes | Pareto endpoint set | which harm/efficiency outcomes cannot be omitted | ranked mandatory endpoints |

Any adopted change maps to participant codes, response items, rationale,
decision owner, date, and protocol/config commit. Expert comments can justify a
policy choice; they cannot replace calibration, invariant tests, or outcome
evaluation.

## 6. Analysis plan

Report, without selectively dropping unfavorable items:

- panel composition and recruitment route;
- completion and missing-response counts;
- per-item median, full range, and distribution;
- individual and aggregate weight/range proposals;
- pairwise agreement for vignette rankings, with ties preserved;
- first-to-second-round movement;
- every unresolved disagreement and minority safety objection;
- declared conflicts, facilitator role, protocol deviations, and ethics status.

For two experts, emphasize raw paired responses and disagreements; do not
present unstable inferential statistics. For larger panels, optional Kendall's
`W` or weighted kappa is descriptive and includes uncertainty. No p-value is a
criterion for deleting a parameter or declaring expert “validation.”

Recommended decision labels are:

- `supported within stated context`;
- `supported with required modification`;
- `contested`;
- `insufficient evidence`;
- `not assessed`.

The label “validated” is permitted only with the panel evidence attached and a
clear domain qualifier. Individual endorsement is never inferred from group
summary statistics.

## 7. Acceptance and change control

C5 is locally complete only as a protocol. External validation passes when:

1. the independence/workshop minimum is met;
2. ethics/consent status is documented;
3. frozen materials and checksums are archived;
4. every parameter row above is linked to actual expert evidence or marked
   `not assessed`;
5. disagreements and negative findings are retained;
6. the signed or appropriately anonymized summary is available to the authors
   and its shareability is declared;
7. any code/policy change is made before the next applicable protocol freeze
   and reruns all affected methods symmetrically.

Expert responses must not be used to reopen test-seed search space. A change
after Gate 2 requires a documented protocol incident and invalidates every
affected test result until symmetric rerun.

## 8. Data handling and auditable artifacts

Store outside the public repository unless consent and institutional policy
explicitly allow otherwise:

- consent records and signatures;
- identities/contact details;
- raw audio/video;
- identifiable transcripts;
- payment records.

The repository may contain a de-identified aggregate summary with participant
codes, the frozen instrument/checksum, response-codebook version, deviations,
and a statement of access restrictions. Never commit secrets or direct
identifiers. Keep a retention/deletion date and responsible custodian in the
study record.

Expected external artifacts are:

```text
expert-study/
  protocol-manifest.json
  participant-information-and-consent.<approved format>
  instrument.<approved format>
  vignette-packet.<approved format>
  deidentified-response-codebook.json
  validation-summary.md
  disagreement-log.md
  ethics-or-exemption-record.<restricted>
```

## 9. Predeclared fallback while external-blocked

No eligible expert, consent record, interview response, signature, or
endorsement is present in the repository as of 2026-07-28. Therefore:

- recruitment and evidence collection remain `external-blocked`;
- current weights/caps/thresholds are illustrative, not practitioner-validated;
- dispatch conclusions remain synthetic/illustrative;
- the paper explicitly lists missing expert validation as an unresolved
  limitation;
- no expert citation, quotation, rationale, agreement statistic, or
  endorsement is fabricated;
- C1–C4 synthetic work may continue, but cannot be described as field
  validation.
