from datetime import datetime, timedelta, timezone
import itertools

from demo.v2.contracts import ReportV2
from demo.v2.dedup import (
    CorroborationPolicyV2,
    NearDuplicatePolicyV2,
    are_near_duplicates,
    capped_distinct_source_corroboration,
    deduplicate_reports,
    exact_fingerprint,
)


NOW = datetime(2026, 8, 11, tzinfo=timezone.utc)


def _report(report_id: str, **overrides: object) -> ReportV2:
    values: dict[str, object] = {
        "report_id": report_id,
        "L": (16.0, 108.0),
        "T": NOW,
        "F": 0.4,
        "E": 0.8,
        "N": 20,
        "V": 3,
        "source_id": f"source-{report_id}",
        "source_family": "citizen",
        "provenance_quality": 0.7,
        "has_image": True,
    }
    values.update(overrides)
    return ReportV2(**values)


def _partition(result: object) -> tuple[tuple[str, ...], ...]:
    families = result.families  # type: ignore[attr-defined]
    return tuple(sorted(tuple(sorted(family.report_ids)) for family in families))


def test_exact_fingerprint_excludes_transport_and_source_id() -> None:
    first = _report("wire-1", source_id="phone-a")
    retransmission = _report("wire-2", source_id="phone-b")
    other_family = _report("wire-3", source_family="agency")

    assert exact_fingerprint(first) == exact_fingerprint(retransmission)
    assert exact_fingerprint(first) != exact_fingerprint(other_family)

    result = deduplicate_reports([first, retransmission, other_family])
    assert result.exact_duplicates_removed == 1
    assert len(result.exact_units) == 2


def test_exact_fingerprint_canonicalizes_signed_numeric_zero() -> None:
    positive = _report("positive", F=0.0, E=0.0, N=0.0, V=0.0)
    negative = _report("negative", F=-0.0, E=-0.0, N=-0.0, V=-0.0)
    assert exact_fingerprint(positive) == exact_fingerprint(negative)


def test_complete_link_prevents_transitive_near_duplicate_chain() -> None:
    # About 80 m and 160 m north of A.  A~B and B~C, but A is not near C.
    latitude_step = 80.0 / 111_195.0
    reports = [
        _report("A", L=(16.0, 108.0)),
        _report("B", L=(16.0 + latitude_step, 108.0)),
        _report("C", L=(16.0 + 2.0 * latitude_step, 108.0)),
    ]
    policy = NearDuplicatePolicyV2(distance_m=100.0)
    assert are_near_duplicates(reports[0], reports[1], policy)
    assert are_near_duplicates(reports[1], reports[2], policy)
    assert not are_near_duplicates(reports[0], reports[2], policy)

    reference = deduplicate_reports(reports, policy)
    assert sorted(len(family.units) for family in reference.families) == [1, 2]
    for family in reference.families:
        for first, second in itertools.combinations(family.representatives, 2):
            assert are_near_duplicates(first, second, policy)

    # Input order cannot decide whether the chain is collapsed.
    reference_partition = _partition(reference)
    for permutation in itertools.permutations(reports):
        assert _partition(deduplicate_reports(permutation, policy)) == reference_partition


def test_near_duplicates_require_matching_masks_and_source_family() -> None:
    complete = _report("a")
    missing_e = _report("b", E=None)
    other_family = _report("c", source_family="agency")
    assert not are_near_duplicates(complete, missing_e)
    assert not are_near_duplicates(complete, other_family)


def test_corroboration_counts_distinct_source_keys_and_caps_them() -> None:
    reports = [
        _report("target", source_family="citizen", source_id="one"),
        _report("same-family", source_family="citizen", source_id="two"),
        _report("agency-1", source_family="agency", source_id="a1"),
        _report("agency-2", source_family="agency", source_id="a2"),
        _report("ngo", source_family="ngo", source_id="n1"),
        _report("radio", source_family="radio", source_id="r1"),
        _report(
            "late",
            source_family="late-source",
            source_id="late",
            T=NOW + timedelta(hours=2),
        ),
        _report("missing-l", source_family="missing", L=None),
    ]
    family_counts = capped_distinct_source_corroboration(
        reports,
        CorroborationPolicyV2(cap=2, independence_key="source_family"),
    )
    assert family_counts["target"] == 2
    assert family_counts["missing-l"] == 0

    source_counts = capped_distinct_source_corroboration(
        reports,
        CorroborationPolicyV2(cap=3, independence_key="source_id"),
    )
    assert source_counts["target"] == 3
