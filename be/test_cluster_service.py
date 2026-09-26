import unittest

from cluster_service import ClusterCache, compute_clusters, to_report_v2


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
        self.assertLessEqual(top["priority"], 1.75)

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
