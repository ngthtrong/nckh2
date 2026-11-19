"""Shared backend lifecycle and benchmark naming; no Docker or phone required."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
import httpx
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import coordinator


class SharedBackendTests(unittest.TestCase):
    def test_dashboard_browser_error_is_recorded_fail_without_password(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            manifest = {'sessionId': 'test-benchmark', 'upstream': 'http://backend.test',
                        'dashboardUrl': 'http://dashboard.test', 'adminUsername': 'admin'}
            with patch.object(coordinator, 'selected_session', return_value=(folder, manifest)), \
                 patch.object(coordinator, 'verify_backend'), \
                 patch.object(coordinator.getpass, 'getpass', return_value='secret-test-password'), \
                 patch.object(coordinator.web, 'api', return_value={'reports': [{'id': 'post-1', 'description': 'Benchmark test-benchmark online'}]}), \
                 patch('playwright.sync_api.sync_playwright', side_effect=RuntimeError('browser error secret-test-password')):
                coordinator.dashboard(SimpleNamespace(benchmark=None, run=1, headed=False))
            saved = json.loads((folder/'dashboard-checks.json').read_text(encoding='utf-8'))
            self.assertEqual(saved['status'], 'FAIL')
            self.assertNotIn('secret-test-password', json.dumps(saved))

    def test_serve_prepares_both_runs_and_reuses_the_same_alternative_checkpoint(self):
        from prepare_assets import benchmark_package
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            name = '2026-10-23_mobile_run_001'
            folder = root / 'benchmarks' / name
            info = benchmark_package(1, folder / 'package.rhe')
            manifest = dict(sessionId=name, package=info, seedRun=1, serverId='same-db',
                            upstream='http://backend.test', appUrl='http://phone.test',
                            dashboardUrl='http://dashboard.test', proxyPort=18101, backendMode='shared')
            with patch.object(coordinator, 'HERE', root), \
                 patch.object(coordinator, 'verify_backend'), \
                 patch.object(coordinator, 'create_app') as create, \
                 patch.object(coordinator.uvicorn, 'run'):
                coordinator.serve(manifest, folder)
                alternatives = create.call_args.kwargs['run_manifests']
                self.assertEqual(len(alternatives), 1)
                other, location = alternatives[0]
                self.assertEqual(other['package']['manifest']['goldRun'], 'run_002')
                checkpoint = location / 'checkpoint-marker.json'
                checkpoint.write_text('preserve', encoding='utf-8')
                coordinator.serve(manifest, folder)
                again, _ = create.call_args.kwargs['run_manifests'][0]
                self.assertEqual(again['package']['sha256'], other['package']['sha256'])
                self.assertEqual(checkpoint.read_text(encoding='utf-8'), 'preserve')

    def test_old_backend_has_actionable_error_without_changing_identity(self):
        for payload in [{'status': 'ok'}, {'serverId': None}, {'serverId': ''}, []]:
            with self.subTest(payload=payload):
                response = httpx.Response(200, json=payload,
                                          request=httpx.Request('GET', 'http://backend.test/healthz'))
                manifest = {'upstream': 'http://backend.test', 'serverId': 'existing-db'}
                with patch.object(coordinator.httpx, 'get', return_value=response), \
                     patch.object(coordinator.httpx, 'Client') as client, \
                     self.assertRaisesRegex(RuntimeError, 'docker compose up -d --build be dashboard'):
                    coordinator.verify_backend(manifest, password='test-password')
                client.assert_not_called()
                self.assertEqual(manifest['serverId'], 'existing-db')

    def test_name_uses_vietnam_time_and_readable_benchmark(self):
        name = coordinator.benchmark_name('mobile_run_001', datetime(2026, 10, 23, 7, 30, tzinfo=timezone.utc))
        self.assertEqual(name, '2026-10-23_14-30-00-000000_mobile_run_001')
        for invalid in ['../bad', '', 'bad/name', 'a' * 50]:
            with self.assertRaises(ValueError):
                coordinator.benchmark_name(invalid)

    def test_start_attaches_without_starting_docker_or_resetting_data(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            options = SimpleNamespace(lan_ip='192.168.1.147', backend_port=8000,
                                      dashboard_port=8080, proxy_port=18101,
                                      seed_run=1, username='admin', benchmark='mobile_run_001')
            with patch.object(coordinator, 'HERE', root), \
                 patch.object(coordinator, 'benchmark_package', return_value={'inputs': {}}), \
                 patch.object(coordinator, 'verify_backend') as verify, \
                 patch.object(coordinator, 'serve') as serve, \
                 patch.object(coordinator.socket, 'socket') as socket_factory, \
                 patch.object(coordinator.getpass, 'getpass', return_value='existing-password'), \
                 patch.object(coordinator.subprocess, 'run') as run:
                coordinator.start(options)
                socket_factory.return_value.__enter__.return_value.bind.assert_called_once_with(('0.0.0.0', 18101))
                run.assert_not_called()
                manifest = serve.call_args.args[0]
                self.assertEqual(manifest['upstream'], 'http://127.0.0.1:8000')
                self.assertEqual(manifest['dashboardUrl'], 'http://127.0.0.1:8080')
                self.assertEqual(manifest['backendMode'], 'shared')
                verify.assert_called_once_with(manifest, password='existing-password')
                folder, loaded = coordinator.load_session(None)
                self.assertEqual(loaded, manifest)
                self.assertEqual(folder.name, manifest['sessionId'])

    def test_select_run_two_for_dashboard_uses_its_own_saved_manifest(self):
        primary = {'sessionId': '2026-10-23_mobile_run_001', 'seedRun': 1,
                   'serverId': 'same-db', 'upstream': 'http://backend.test'}
        other = dict(primary, seedRun=2, sessionId=primary['sessionId']+'_run_002')
        with patch.object(coordinator, 'load_session', side_effect=[(Path('one'), primary), (Path('two'), other)]) as load:
            folder, selected = coordinator.selected_session(SimpleNamespace(benchmark=None, run=2))
        self.assertEqual(folder, Path('two'))
        self.assertEqual(selected['seedRun'], 2)
        self.assertEqual(load.call_args.args[0], other['sessionId'])

    def test_shared_backend_auth_does_not_require_gold_seed_reports(self):
        paths = []
        def backend(request):
            paths.append(request.url.path)
            if request.url.path == '/healthz':
                return httpx.Response(200, json={'serverId': 'shared-db'})
            if request.url.path == '/api/auth/login':
                return httpx.Response(200, json={'token': 'test-token'})
            if request.url.path == '/api/auth/me':
                return httpx.Response(200, json={'role': 'admin'})
            if request.url.path == '/api/auth/logout':
                return httpx.Response(200, json={})
            raise AssertionError('Unexpected shared DB request: ' + request.url.path)
        manifest = {'upstream': 'http://backend.test', 'adminUsername': 'admin'}
        client = httpx.Client(base_url=manifest['upstream'], transport=httpx.MockTransport(backend))
        health = httpx.Response(200, json={'serverId': 'shared-db'},
                                request=httpx.Request('GET', 'http://backend.test/healthz'))
        with patch.object(coordinator.httpx, 'get', return_value=health), \
             patch.object(coordinator.httpx, 'Client', return_value=client):
            coordinator.verify_backend(manifest, password='test-password')
        self.assertEqual(manifest['serverId'], 'shared-db')
        self.assertNotIn('/api/reports', paths)

    def test_stop_never_stops_shared_docker(self):
        manifest = {'backendMode': 'shared'}
        with patch.object(sys, 'argv', ['coordinator.py', 'stop']), \
             patch.object(coordinator, 'load_session', return_value=(Path('.'), manifest)), \
             patch.object(coordinator.subprocess, 'run') as run:
            coordinator.main()
            run.assert_not_called()

    def test_old_private_backend_requires_new_benchmark(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root / 'benchmarks' / 'old'
            folder.mkdir(parents=True)
            (folder / 'manifest.json').write_text(json.dumps({'sessionId': 'old'}))
            with patch.object(coordinator, 'HERE', root), self.assertRaisesRegex(ValueError, 'benchmark'):
                coordinator.load_session('old')


if __name__ == '__main__':
    unittest.main()
