"""Both runs are reusable APK inputs, independent of benchmark timestamps."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
import httpx
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build_package import MODEL, read_package, sha, web


class BundledAssetsTests(unittest.TestCase):
    def test_static_packages_bind_to_two_live_runs_without_download_or_rebuild(self):
        from prepare_assets import benchmark_package
        from mobile_api import create_app
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            packages = [benchmark_package(i, folder/f'run_{i:03d}'/'package.rhe') for i in (1, 2)]
            manifests = [dict(sessionId=f'2026-10-23_16-00-00_mobile_run_{i:03d}',
                              package=packages[i-1], upstream='http://backend.test', serverId='same-db') for i in (1, 2)]
            def backend(request):
                return httpx.Response(200, json={'authenticated': True, 'role': 'admin'})
            app = create_app(manifests[0], folder/'run_001', transport=httpx.MockTransport(backend),
                             run_manifests=[(manifests[1], folder/'run_002')])
            with TestClient(app) as client:
                headers = {'Authorization': 'Bearer test'}
                runs = client.get('/api/experiments/e2e/runs', headers=headers).json()['runs']
                self.assertEqual([r['goldRun'] for r in runs], ['run_001', 'run_002'])
                for index, run in enumerate(runs):
                    self.assertEqual(run['packageSha256'], packages[index]['sha256'])
                    prefix = run['controlPath']+'/api/experiments/e2e'
                    result = client.post(prefix+'/claim', headers=headers,
                                         json={'installationId':'phone', 'packageSha256':run['packageSha256']})
                    result.raise_for_status()
                    self.assertEqual(result.json()['sessionId'], manifests[index]['sessionId'])
                    self.assertEqual(result.json()['serverId'], 'same-db')
                    self.assertNotIn('sessionId', result.json()['fixture'])
                self.assertEqual(client.get('/api/experiments/e2e/runs').status_code, 401)

    @unittest.skipUnless(MODEL.is_file() and (web.IMAGE_ROOT/'high/flood_4800.jpg').is_file(), 'Regenerating assets requires the optional training sources')
    def test_prepare_builds_two_static_runs_and_keeps_seed1024_model(self):
        from prepare_assets import prepare_assets, verify_assets
        with tempfile.TemporaryDirectory() as temp:
            assets = Path(temp)
            catalog = prepare_assets(assets)
            self.assertEqual([r['goldRun'] for r in catalog['runs']], ['run_001', 'run_002'])
            self.assertEqual(catalog, verify_assets(assets))
            original = json.dumps(catalog, sort_keys=True)
            for item in catalog['runs']:
                data = (assets / 'benchmarks/mobile' / item['file']).read_bytes()
                manifest, _ = read_package(data)
                self.assertEqual(manifest['schemaVersion'], 2)
                self.assertNotIn('sessionId', manifest)
                self.assertEqual(sha(data), item['packageSha256'])
                self.assertEqual(manifest['model']['seed'], 1024)
                self.assertEqual(manifest['model']['sha256'], sha((assets/'models/model.pte').read_bytes()))
            self.assertEqual(json.dumps(prepare_assets(assets), sort_keys=True), original)
            path = assets/'benchmarks/mobile/run_002.rhe'
            path.write_bytes(path.read_bytes()[:-1] + b'!')
            with self.assertRaises(ValueError):
                verify_assets(assets)


if __name__ == '__main__':
    unittest.main()
