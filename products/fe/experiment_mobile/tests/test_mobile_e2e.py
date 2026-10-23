"""Kiểm tra gói E2E, quyền admin và tính toàn vẹn session; không dùng Docker/điện thoại."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
import httpx
from fastapi.testclient import TestClient

FOLDER = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(FOLDER))


class PackageTests(unittest.TestCase):
    def test_dashboard_requires_current_mobile_reports(self):
        from coordinator import dashboard_mobile_targets
        with self.assertRaises(ValueError):
            dashboard_mobile_targets('unit-session', [{'id': 'sim-1', 'description': 'seed'}])
        targets = dashboard_mobile_targets('unit-session', [
            {'id': 'sim-1', 'description': 'seed'},
            {'id': 'post-1', 'description': 'Benchmark unit-session online'},
            {'id': 'post-2', 'description': 'Benchmark other-session online'}])
        self.assertEqual(targets, ['post-1'])
    def test_run_images_and_package_integrity(self):
        from build_package import read_package
        from prepare_assets import benchmark_package
        with tempfile.TemporaryDirectory() as folder:
            for run, label in [(1, 'high'), (2, 'medium')]:
                path = Path(folder) / f'{run}.rhe'
                info = benchmark_package(run, path)
                manifest, image = read_package(path.read_bytes())
                self.assertEqual(manifest['goldRun'], f'run_{run:03d}')
                self.assertEqual(manifest['image']['label'], label)
                self.assertNotIn('sessionId', manifest)
                self.assertEqual(len(image), manifest['image']['length'])
                self.assertEqual(info['manifest'], manifest)
                self.assertEqual(len(list((path.parent/'inputs'/manifest['goldRun']).glob('*.json'))), 2)
                corrupt = bytearray(path.read_bytes())
                corrupt[-1] ^= 1
                with self.assertRaises(ValueError):
                    read_package(bytes(corrupt))

    def test_run_outside_range_is_rejected(self):
        from prepare_assets import benchmark_package
        with tempfile.TemporaryDirectory() as folder, self.assertRaises(ValueError):
            benchmark_package(81, Path(folder) / 'bad.rhe')


class CoordinatorTests(unittest.TestCase):
    def setUp(self):
        from prepare_assets import benchmark_package
        from mobile_api import create_app
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        folder = Path(self.temp.name)
        info = benchmark_package(1, folder / 'package.rhe')
        self.manifest = dict(sessionId='unit-session', package=info, upstream='http://backend.test',
                             dashboardUrl='http://dashboard.test', deviceClaim=None)
        self.backend_reports = []
        self.status_updates = []
        def backend(request):
            if request.url.path == '/api/auth/me':
                token = request.headers.get('authorization')
                return httpx.Response(200, json={'authenticated': bool(token), 'role': 'admin' if token == 'Bearer admin-test' else 'operator'})
            if request.url.path == '/api/reports':
                return httpx.Response(200, json={'reports': self.backend_reports})
            if request.method == 'PATCH':
                self.status_updates.append(request.url.path)
            if request.url.path == '/api/clusters':
                return httpx.Response(200, json={'review': [], 'clusters': []})
            if request.url.path == '/sync/messages':
                return httpx.Response(200, json={'received': json.loads(request.content)})
            if request.url.path == '/probe':
                return httpx.Response(200, content=b'x' * 2048)
            return httpx.Response(200, json={'status': 'ok', 'serverId': '0123456789abcdef'})
        second = dict(self.manifest, sessionId='unit-session-run_002',
                      package=benchmark_package(2, folder / 'run_002/package.rhe'))
        self.client = TestClient(create_app(self.manifest, folder, transport=httpx.MockTransport(backend),
                                           run_manifests=[(second, folder / 'run_002')]))
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)

    def test_admin_gate_and_bound_run(self):
        self.assertEqual(self.client.get('/api/experiments/e2e/runs').status_code, 401)
        self.assertEqual(self.client.get('/api/experiments/e2e/runs', headers={'Authorization': 'Bearer operator'}).status_code, 403)
        headers = {'Authorization': 'Bearer admin-test'}
        self.assertEqual(self.client.get('/api/experiments/e2e/runs', headers=headers).json()['runs'][0]['goldRun'], 'run_001')
        runs = self.client.get('/api/experiments/e2e/runs', headers=headers).json()['runs']
        self.assertEqual([r['goldRun'] for r in runs], ['run_001', 'run_002'])
        from build_package import read_package
        response = self.client.get('/api/experiments/e2e/package?run=run_002', headers=headers)
        self.assertEqual(read_package(response.content)[0]['goldRun'], 'run_002')
        second = self.client.get(runs[1]['controlPath'] + '/api/experiments/e2e/session', headers=headers)
        self.assertEqual(second.json()['sessionId'], 'unit-session-run_002')
        self.assertEqual(self.client.get('/api/experiments/e2e/session', headers=headers).json()['sessionId'], 'unit-session')

    def test_shared_db_filters_benchmark_and_refuses_foreign_feedback(self):
        headers = {'Authorization': 'Bearer admin-test'}
        self.backend_reports = [
            {'id': 'mine', 'description': 'Benchmark unit-session online'},
            {'id': 'other', 'description': 'Benchmark other-session online'},
            {'id': 'seed', 'description': 'seed report'},
        ]
        self.client.post('/api/experiments/e2e/claim', headers=headers,
                         json={'installationId': 'device', 'packageSha256': self.manifest['package']['sha256']}).raise_for_status()
        observed = self.client.get('/api/experiments/e2e/observations', headers=headers).json()
        self.assertEqual([r['id'] for r in observed['reports']], ['mine'])
        response = self.client.post('/api/experiments/e2e/feedback/other', headers=headers,
                                    json={'installationId': 'device'})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.status_updates, [])

    def test_second_run_keeps_its_session_results_and_shared_network_profile(self):
        headers = {'Authorization': 'Bearer admin-test'}
        run = self.client.get('/api/experiments/e2e/runs', headers=headers).json()['runs'][1]
        prefix = run['controlPath'] + '/api/experiments/e2e'
        identity = {'installationId': 'device', 'packageSha256': run['packageSha256']}
        self.client.post(prefix + '/claim', headers=headers, json=identity).raise_for_status()
        self.client.post(prefix + '/profile', headers=headers,
                         json={'installationId': 'device', 'profile': 'offline'}).raise_for_status()
        self.assertEqual(self.client.post('/sync/messages', json={}).status_code, 503)
        self.client.post(prefix + '/profile', headers=headers,
                         json={'installationId': 'device', 'profile': 'online'}).raise_for_status()
        self.backend_reports = [
            {'id': 'mine', 'description': 'Benchmark unit-session-run_002 online attempt 123'},
            {'id': 'other', 'description': 'Benchmark unit-session online'},
        ]
        body = dict(identity, sessionId=run['sessionId'], environment={}, reports={'online': 'mine'},
                    inference={}, checks=[{'stage': 'online', 'status': 'PASS', 'method': 'app', 'detail': 'retry'}])
        result = self.client.post(prefix + '/results', headers=headers, json=body)
        result.raise_for_status()
        self.assertEqual(result.json()['checks'][0]['status'], 'PASS')
        self.assertTrue((Path(self.temp.name) / 'run_002/results/unknown/unit-session-run_002/unit-session-run_002.json').is_file())
        body['reports']['online'] = 'other'
        result = self.client.post(prefix + '/results', headers=headers, json=body)
        self.assertEqual(result.json()['checks'][0]['status'], 'FAIL')
        self.backend_reports[0]['description'] += ' invalid'
        body['reports']['online'] = 'mine'
        result = self.client.post(prefix + '/results', headers=headers, json=body)
        self.assertEqual(result.json()['checks'][0]['status'], 'FAIL')

    def test_profile_blocks_data_but_keeps_control(self):
        headers = {'Authorization': 'Bearer admin-test'}
        claim = self.client.post('/api/experiments/e2e/claim', headers=headers, json={'installationId': 'device-test', 'packageSha256': self.manifest['package']['sha256']})
        self.assertEqual(claim.status_code, 200)
        profile = self.client.post('/api/experiments/e2e/profile', headers=headers, json={'profile': 'offline', 'installationId': 'device-test'})
        self.assertEqual(profile.status_code, 200)
        self.assertEqual(self.client.post('/sync/messages', json={}).status_code, 503)
        self.assertEqual(self.client.get('/healthz').status_code, 200)
        self.assertEqual(self.client.get('/api/experiments/e2e/session', headers=headers).status_code, 200)

    def test_other_installation_cannot_take_session(self):
        headers = {'Authorization': 'Bearer admin-test'}
        for identity, expected in [('device-a', 200), ('device-b', 409)]:
            response = self.client.post('/api/experiments/e2e/claim', headers=headers, json={'installationId': identity, 'packageSha256': self.manifest['package']['sha256']})
            self.assertEqual(response.status_code, expected)

    def test_results_cannot_invent_server_or_dashboard_pass(self):
        headers = {'Authorization': 'Bearer admin-test'}
        identity = {'installationId': 'device-a', 'packageSha256': self.manifest['package']['sha256']}
        self.client.post('/api/experiments/e2e/claim', headers=headers, json=identity).raise_for_status()
        body = dict(identity, sessionId='unit-session', environment={'device': {'model': 'test-device'}},
                    checks=[{'stage': stage, 'status': 'PASS', 'method': 'app', 'detail': 'claimed'}
                            for stage in ['online', 'dashboard']], reports={'online': 'missing'}, inference={}, evidence={})
        response = self.client.post('/api/experiments/e2e/results', headers=headers, json=body)
        self.assertEqual(response.status_code, 200)
        saved = Path(self.temp.name) / 'results/test-device/unit-session'
        self.assertTrue((saved / 'unit-session.json').is_file())
        self.assertTrue((saved / 'unit-session.csv').is_file())
        self.assertEqual(len(list((saved / 'attempts').glob('*.json'))), 1)
        checks = {c['stage']: c['status'] for c in response.json()['checks']}
        self.assertEqual(checks['online'], 'FAIL')
        self.assertEqual(checks['dashboard'], 'NOT_RUN')
        self.assertEqual(checks['manual_android_ui'], 'NOT_RUN')
        self.assertEqual(checks['manual_physical_network'], 'NOT_RUN')
        self.assertFalse(response.json()['automaticComplete'])
        body['evidence'] = {'authorization': 'must-not-save'}
        self.assertEqual(self.client.post('/api/experiments/e2e/results', headers=headers, json=body).status_code, 422)

    def test_restart_requires_new_dashboard_evidence(self):
        headers = {'Authorization': 'Bearer admin-test'}
        identity = {'installationId': 'device', 'packageSha256': self.manifest['package']['sha256']}
        self.client.post('/api/experiments/e2e/claim', headers=headers, json=identity).raise_for_status()
        dashboard = Path(self.temp.name) / 'dashboard-checks.json'
        dashboard.write_text(json.dumps({'status': 'PASS', 'mobileReportIds': [],
                                         'atUtc': '2026-10-23T01:00:00+00:00'}), encoding='utf-8')
        body = dict(identity, sessionId='unit-session', environment={}, checks=[], reports={}, inference={},
                    evidence={'attemptStartedAtUtc': '2026-10-23T02:00:00.000Z'})
        result = self.client.post('/api/experiments/e2e/results', headers=headers, json=body)
        checks = {c['stage']: c['status'] for c in result.json()['checks']}
        self.assertEqual(checks['dashboard'], 'NOT_RUN')

    def test_manual_failure_is_saved_to_csv_once_and_kept_after_retest(self):
        import csv
        headers = {'Authorization': 'Bearer admin-test'}
        identity = {'installationId': 'device', 'packageSha256': self.manifest['package']['sha256']}
        self.client.post('/api/experiments/e2e/claim', headers=headers, json=identity).raise_for_status()
        event = {'id': 'manual-error-1', 'atUtc': '2026-10-23T09:00:00Z', 'stage': 'manual_android_ui',
                 'status': 'FAIL', 'detail': 'Lịch sử thiếu ảnh', 'reportId': 'post-1', 'evidenceFile': 'case7.png'}
        body = dict(identity, sessionId='unit-session', environment={'device': {'model': 'phone'}},
                    checks=[{'stage': 'manual_android_ui', 'status': 'FAIL', 'method': 'manual', 'detail': event['detail']}],
                    reports={}, inference={}, evidence={'manualChecks': [event]})
        for _ in range(2):
            self.client.post('/api/experiments/e2e/results', headers=headers, json=body).raise_for_status()
        log = Path(self.temp.name)/'results/phone/unit-session/loi_thu_cong.csv'
        with log.open(encoding='utf-8-sig', newline='') as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['loi_thuc_te'], event['detail'])
        self.assertEqual(rows[0]['case'], '7')
        self.assertEqual(rows[0]['id_bao_cao'], 'post-1')
        body['checks'][0]['status'] = 'PASS'
        self.client.post('/api/experiments/e2e/results', headers=headers, json=body).raise_for_status()
        with log.open(encoding='utf-8-sig', newline='') as stream:
            self.assertEqual(len(list(csv.DictReader(stream))), 1)

    def test_dashboard_failed_evidence_is_logged_and_cannot_be_confirmed_pass_by_app(self):
        import csv
        headers = {'Authorization': 'Bearer admin-test'}
        identity = {'installationId': 'device', 'packageSha256': self.manifest['package']['sha256']}
        self.client.post('/api/experiments/e2e/claim', headers=headers, json=identity).raise_for_status()
        (Path(self.temp.name)/'dashboard-checks.json').write_text(json.dumps(
            {'status': 'FAIL', 'mobileReportIds': [], 'atUtc': '2026-10-23T09:00:00Z',
             'checks': [{'status': 'FAIL', 'detail': 'Sai nội dung bài trên dashboard'}]}), encoding='utf-8')
        body = dict(identity, sessionId='unit-session', environment={}, reports={}, inference={},
                    checks=[{'stage': 'dashboard', 'status': 'PASS', 'method': 'manual', 'detail': 'claimed'}])
        result = self.client.post('/api/experiments/e2e/results', headers=headers, json=body)
        result.raise_for_status()
        self.assertEqual(next(c['status'] for c in result.json()['checks'] if c['stage']=='dashboard'), 'FAIL')
        with (Path(self.temp.name)/'results/unknown/unit-session/loi_thu_cong.csv').open(encoding='utf-8-sig', newline='') as stream:
            self.assertEqual(list(csv.DictReader(stream))[0]['case'], '9')

    def test_proxy_forwards_real_request_body(self):
        response = self.client.post('/sync/messages', json={'hello': 'mobile'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['received'], {'hello': 'mobile'})

    def test_profile_20_actually_throttles_download(self):
        headers = {'Authorization': 'Bearer admin-test'}
        identity = {'installationId': 'device-rate', 'packageSha256': self.manifest['package']['sha256']}
        self.client.post('/api/experiments/e2e/claim', headers=headers, json=identity).raise_for_status()
        self.client.post('/api/experiments/e2e/profile', headers=headers,
                         json={'installationId': 'device-rate', 'profile': '20'}).raise_for_status()
        started = time.monotonic()
        response = self.client.get('/probe')
        self.assertEqual(response.content, b'x' * 2048)
        self.assertGreaterEqual(time.monotonic() - started, .9)  # 0.8192 s body + 0.15 s RTT


if __name__ == '__main__':
    unittest.main()
