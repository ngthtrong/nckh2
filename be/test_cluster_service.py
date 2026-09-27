import math
import unittest
from datetime import datetime, timedelta, timezone

import numpy as np

from cluster_service import DEFAULT_GRAPH_CONFIG, ClusterCache, compute_clusters, to_report_v2
from rescue_core import PriorityPolicyV2, ReportV2
from rescue_core.clustering import _pair_weight_matrix
from rescue_core.dedup import confidence_scores, deduplicate_reports
from rescue_core.similarity import SimilarityParamsV2, product_similarity


def _report(rec_id, lat, lng, minute, **extra):
    base = {
        "id": rec_id,
        "lat": lat,
        "lng": lng,
        "createdAt": f"2026-09-24T08:{minute:02d}:00+00:00",
        "serverReceivedAt": "2026-09-24T08:59:00",
        "trappedCount": 3,
        "injuredCount": 0,
        "vulnerableGroups": [],
        "description": "Nhà bị ngập, có người mắc kẹt",
        "aiTags": [{"label": "Ngập sâu (High)", "confidence": 0.9}],
        "status": "processing",
        "statusVersion": 1,
        "imageUrl": None,
        "payload": {},
    }
    base.update(extra)
    return base


def _two_incidents():
    # Hai điểm nóng cách nhau ~20 km, mỗi điểm 6 báo cáo trong bán kính ~100 m.
    reports = []
    for i in range(6):
        reports.append(_report(f"a{i}", 16.0600 + i * 0.0002, 108.2200 + i * 0.0002, i))
        reports.append(_report(f"b{i}", 15.8800 + i * 0.0002, 108.3300 + i * 0.0002, i,
                               aiTags=[{"label": "Ngập nhẹ (Low)", "confidence": 0.8}],
                               description="Cần hỗ trợ lương thực"))
    return reports


class ToReportV2Test(unittest.TestCase):
    def test_maps_app_fields(self):
        r = to_report_v2(_report("x", 16.0, 108.0, 5, vulnerableGroups=["elderly", "children"], injuredCount=2))
        self.assertEqual(r.L, (16.0, 108.0))
        self.assertEqual(r.F, 1.0)
        self.assertEqual(r.E, 0.75)
        self.assertEqual(r.N, 5.0)
        self.assertEqual(r.V, 2.0)
        self.assertEqual(r.provenance_quality, 0.9)
        self.assertTrue(r.graph_eligible)

    def test_non_flood_label_and_missing_text(self):
        r = to_report_v2(_report("x", 16.0, 108.0, 5, description="", aiTags=[{"label": "Không ngập nước", "confidence": 0.7}]))
        self.assertEqual(r.F, 0.0)
        self.assertIsNone(r.E)

    def test_payload_algorithm_fields_take_precedence(self):
        payload = {"flood": 0.55, "urgency": 0.6, "n_trapped": 16, "vulnerability": 0.44, "confidence": 0.95}
        r = to_report_v2(_report("x", 16.0, 108.0, 5, payload=payload))
        self.assertEqual((r.F, r.E, r.N, r.V, r.provenance_quality), (0.55, 0.6, 16.0, 0.44, 0.95))

    def test_epoch_ms_created_at(self):
        r = to_report_v2(_report("x", 16.0, 108.0, 5, createdAt="1790065506614"))
        self.assertEqual(r.T.year, 2026)


class ComputeClustersTest(unittest.TestCase):
    def test_separates_distant_incidents(self):
        result = compute_clusters(_two_incidents())
        groups = [set(c["reportIds"]) for c in result["clusters"]]
        for group in groups:
            prefixes = {report_id[0] for report_id in group}
            self.assertEqual(len(prefixes), 1, f"cụm trộn hai điểm nóng: {group}")
        self.assertEqual(set().union(*groups), {f"{p}{i}" for p in "ab" for i in range(6)})

    def test_high_flood_incident_ranks_first(self):
        result = compute_clusters(_two_incidents())
        top = result["clusters"][0]
        self.assertTrue(all(report_id.startswith("a") for report_id in top["reportIds"]))
        self.assertEqual(top["rank"], 1)
        self.assertLessEqual(top["priority"], 2.0)

    def test_missing_location_goes_to_review(self):
        reports = _two_incidents() + [_report("nogps", None, None, 3)]
        result = compute_clusters(reports)
        self.assertIn("nogps", result["review"])
        self.assertNotIn("nogps", {rid for c in result["clusters"] for rid in c["reportIds"]})

    def test_resolved_reports_excluded(self):
        reports = _two_incidents()
        for r in reports:
            if r["id"].startswith("b"):
                r["status"] = "resolved"
        result = compute_clusters(reports)
        self.assertEqual(result["totalReports"], 6)
        self.assertTrue(all(rid.startswith("a") for c in result["clusters"] for rid in c["reportIds"]))

    def test_deterministic(self):
        self.assertEqual(compute_clusters(_two_incidents()), compute_clusters(_two_incidents()))

    def test_empty(self):
        self.assertEqual(compute_clusters([])["clusters"], [])


_T0 = datetime(2026, 9, 24, 8, 0, tzinfo=timezone.utc)


def _v2(report_id, north_m=0.0, minute=0.0, **fields):
    base = dict(F=0.8, E=0.7, N=4.0, V=1.0, has_image=False)
    base.update(fields)
    lat = 16.0 + north_m / 111_195.0
    return ReportV2(report_id=report_id, L=(lat, 108.0), T=_T0 + timedelta(minutes=minute), **base)


class PaperFormulaTest(unittest.TestCase):
    """Công thức phải khớp bài báo ISDS 2026 #6444 (Eq. 1-4)."""

    def test_pair_matrix_matches_scalar_product_similarity(self):
        reports = [_v2("a"), _v2("b", 300, 20, F=None), _v2("c", 900, 50, E=None, F=None), _v2("d", 50, 5, F=0.2)]
        cfg = DEFAULT_GRAPH_CONFIG
        params = SimilarityParamsV2(sigma_geo_m=cfg.sigma_geo_m, tau_t=cfg.tau_t, tau_F=cfg.tau_F,
                                    tau_E=cfg.tau_E, beta=cfg.beta, gamma=cfg.gamma, theta=0.0)
        matrix = _pair_weight_matrix(reports, list(range(len(reports))), cfg)
        for i, first in enumerate(reports):
            for j, second in enumerate(reports):
                expected = 0.0 if i == j else product_similarity(first, second, params)
                self.assertAlmostEqual(matrix[i, j], expected, places=12)

    def test_confidence_eq1_counts_distinct_payloads(self):
        lone = confidence_scores([_v2("a", has_image=True)])
        self.assertAlmostEqual(lone["a"], 1 / (1 + math.exp(-(-0.2 + 1.4))))
        # Hai bản sao y hệt của b chỉ tính là một payload củng cố cho a,
        # và bản sao của chính a không củng cố a.
        reports = [_v2("a"), _v2("a2"), _v2("b1", 200, 10, F=0.3), _v2("b2", 200, 10, F=0.3)]
        q = confidence_scores(reports)
        self.assertAlmostEqual(q["a"], 1 / (1 + math.exp(-(-0.2 + 0.9 * math.log1p(1)))))
        self.assertEqual(q["a"], q["a2"])
        # Ngoài 400 m hoặc 60 phút thì không củng cố.
        far = confidence_scores([_v2("a"), _v2("x", 450, 0, F=0.3), _v2("y", 0, 61, F=0.3)])
        self.assertAlmostEqual(far["a"], 1 / (1 + math.exp(0.2)))

    def test_near_duplicates_are_connected_components(self):
        # A~B và B~C (cách 80 m) nhưng A và C cách 160 m: bài báo gom cả ba (bắc cầu).
        reports = [_v2("A"), _v2("B", 80), _v2("C", 160)]
        result = deduplicate_reports(reports, confidence=confidence_scores(reports))
        self.assertEqual(len(result.families), 1)
        self.assertEqual(result.near_units_coalesced, 2)

    def test_priority_constants_match_paper(self):
        policy = PriorityPolicyV2()
        self.assertEqual((policy.weight_E, policy.weight_F, policy.weight_N), (0.34, 0.33, 0.33))
        self.assertEqual((policy.vulnerability_mu, policy.vulnerability_scale), (2.0, 10.0))
        self.assertEqual((policy.n_ref, policy.v_claim_cap), (500.0, 50.0))

    def test_threshold_uses_all_eligible_pairs(self):
        # 70 báo cáo > 64 láng giềng của candidate pool cũ: vẫn xét đủ mọi cặp.
        reports = [_v2(f"r{i:02d}", 30.0 * i, i % 7) for i in range(70)]
        result = compute_clusters([
            {"id": r.report_id, "lat": r.L[0], "lng": r.L[1], "createdAt": r.T.isoformat(),
             "status": "processing", "payload": {"flood": 0.8, "urgency": 0.7, "n_trapped": 4, "vulnerability": 1}}
            for r in reports
        ])
        self.assertEqual(result["candidatePairs"], 70 * 69 // 2)
        self.assertTrue(np.isfinite(result["clusters"][0]["priority"]))


class ClusterCacheTest(unittest.TestCase):
    def test_recomputes_only_on_change(self):
        cache = ClusterCache()
        reports = _two_incidents()
        first = cache.get(reports)
        self.assertIs(cache.get(list(reports)), first)
        reports[0] = dict(reports[0], status="dispatched", statusVersion=2)
        self.assertIsNot(cache.get(reports), first)


if __name__ == "__main__":
    unittest.main()
