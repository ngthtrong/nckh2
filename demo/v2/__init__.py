"""Isolated version-2 contracts and inference primitives.

Importing this package has no experiment, tuning, artifact, or network side
effects.  Protocol modules may coexist under :mod:`demo.v2` without being
re-exported from this inference-facing surface.
"""

from .contracts import (
    IncidentTruthV2,
    ObservationMaskV2,
    ReportV2,
    TruthV2,
    incident_truth_v2,
    report_v2,
    truth_v2,
    validate_unique_report_ids,
)
from .dedup import (
    CorroborationPolicyV2,
    DeduplicationResultV2,
    EvidenceFamilyV2,
    ExactEvidenceUnitV2,
    NearDuplicatePolicyV2,
    are_near_duplicates,
    capped_distinct_source_corroboration,
    collapse_exact_duplicates,
    complete_link_near_duplicate_families,
    deduplicate_reports,
    exact_fingerprint,
    observable_payload,
)
from .graph import (
    SparseEdgeV2,
    SparseGraphV2,
    build_dense_product_oracle,
    build_sparse_product_graph,
    build_sparse_spatial_edge_list,
    edge_list_to_dense,
    sparse_dense_equivalent,
    split_graph_eligible,
)
from .similarity import (
    ProductBoundV2,
    SimilarityParamsV2,
    context_similarity,
    geographic_similarity,
    haversine_m,
    product_distance_bound,
    product_similarity,
    temporal_similarity,
)

__all__ = [
    "CorroborationPolicyV2",
    "DeduplicationResultV2",
    "EvidenceFamilyV2",
    "ExactEvidenceUnitV2",
    "IncidentTruthV2",
    "NearDuplicatePolicyV2",
    "ObservationMaskV2",
    "ProductBoundV2",
    "ReportV2",
    "SimilarityParamsV2",
    "SparseEdgeV2",
    "SparseGraphV2",
    "TruthV2",
    "are_near_duplicates",
    "build_dense_product_oracle",
    "build_sparse_product_graph",
    "build_sparse_spatial_edge_list",
    "capped_distinct_source_corroboration",
    "collapse_exact_duplicates",
    "complete_link_near_duplicate_families",
    "context_similarity",
    "deduplicate_reports",
    "edge_list_to_dense",
    "exact_fingerprint",
    "geographic_similarity",
    "haversine_m",
    "incident_truth_v2",
    "observable_payload",
    "product_distance_bound",
    "product_similarity",
    "report_v2",
    "sparse_dense_equivalent",
    "split_graph_eligible",
    "temporal_similarity",
    "truth_v2",
    "validate_unique_report_ids",
]
