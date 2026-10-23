"""API admin cho gói/session/kết quả và proxy giới hạn mạng; chỉ chạy trong coordinator thử nghiệm."""
from __future__ import annotations

import asyncio
from collections import Counter
from contextlib import AsyncExitStack, asynccontextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import time

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, Response, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from build_package import STAGES, read_package, sha
from manual_errors import save_manual_errors

PREFIX = '/api/experiments/e2e'
PROFILES = {'online': {'kbps': None, 'rttMs': 0}, 'offline': {'blocked': True},
            '300': {'kbps': 300, 'rttMs': 150}, '20': {'kbps': 20, 'rttMs': 150}}
HOP = {'host', 'connection', 'keep-alive', 'transfer-encoding', 'content-length',
       'content-encoding', 'proxy-authorization', 'proxy-authenticate', 'te', 'trailer', 'upgrade'}


def atomic_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_suffix(path.suffix + '.part')
    part.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    part.replace(path)


class Owner(BaseModel):
    model_config = ConfigDict(extra='forbid')
    installationId: str = Field(pattern=r'^[A-Za-z0-9_-]{1,80}$')


class Claim(Owner):
    packageSha256: str = Field(pattern=r'^[a-f0-9]{64}$')


class ProfileChange(Owner):
    profile: str


class Check(BaseModel):
    model_config = ConfigDict(extra='forbid')
    stage: str
    status: str = Field(pattern=r'^(PASS|FAIL|NOT_RUN)$')
    detail: str = Field(max_length=2000)
    method: str = Field(pattern=r'^(app|manual|coordinator)$')


class Results(Claim):
    sessionId: str
    environment: dict
    checks: list[Check] = Field(max_length=40)
    reports: dict[str, str]
    inference: dict
    evidence: dict = Field(default_factory=dict)


def create_app(manifest: dict, folder: Path, *, transport=None, results_root: Path | None = None,
               run_manifests=(), shared_control=None):
    folder = Path(folder)
    package = Path(manifest['package']['path'])
    data = package.read_bytes()
    fixture, _ = read_package(data)
    if sha(data) != manifest['package']['sha256'] or (fixture.get('sessionId') is not None and fixture['sessionId'] != manifest['sessionId']):
        raise ValueError('Manifest/gói không cùng benchmark hoặc sai hash')
    control_file = folder / 'control.json' if shared_control is None else shared_control[1]
    control = (json.loads(control_file.read_text(encoding='utf-8')) if control_file.exists()
               else {'profile': 'online', 'installationId': None}) if shared_control is None else shared_control[0]
    # Recovery always starts online; record the previous profile rather than silently reusing a blocked link.
    previous_profile = control.get('profile')
    control['profile'] = 'online'
    def save_control():
        atomic_json(control_file, control)
        if folder / 'control.json' != control_file:
            atomic_json(folder / 'control.json', control)
    save_control()
    client = httpx.AsyncClient(base_url=manifest['upstream'], timeout=90, transport=transport, follow_redirects=False)
    children = []

    @asynccontextmanager
    async def lifespan(app):
        async with AsyncExitStack() as stack:
            await stack.enter_async_context(client)
            for child in children:
                await stack.enter_async_context(child.router.lifespan_context(child))
            yield

    app = FastAPI(title='Mobile E2E coordinator (test only)', lifespan=lifespan)
    catalog = {fixture['goldRun']: (manifest, folder, '')}
    for other, other_folder in run_manifests:
        run = other['package']['manifest']['goldRun']
        if not re.fullmatch(r'run_\d{3}', run) or run in catalog:
            raise ValueError('Run không hợp lệ hoặc trùng')
        route = '/mobile-e2e/' + run
        child = create_app(other, other_folder, transport=transport, results_root=results_root,
                           shared_control=(control, control_file))
        children.append(child)
        app.mount(route, child)
        catalog[run] = (other, Path(other_folder), route)

    async def admin(request: Request):
        token = request.headers.get('Authorization', '')
        if not token.startswith('Bearer '):
            raise HTTPException(401, 'Đăng nhập admin của backend thử nghiệm trước')
        try:
            response = await client.get('/api/auth/me', headers={'Authorization': token})
            identity = response.json()
        except (httpx.HTTPError, ValueError):
            raise HTTPException(503, 'Backend chưa sẵn sàng')
        if response.status_code != 200 or not identity.get('authenticated'):
            raise HTTPException(401, 'Phiên đã hết hạn')
        if identity.get('role') != 'admin':
            raise HTTPException(403, 'Chỉ admin được dùng E2E')
        return {'Authorization': token}

    def owner(body: Owner):
        if control['installationId'] != body.installationId:
            raise HTTPException(409, 'Benchmark thuộc lần cài app khác')

    def public_session():
        return {'sessionId': manifest['sessionId'], 'goldRun': fixture['goldRun'], 'serverId': manifest.get('serverId'),
                'packageSha256': manifest['package']['sha256'], 'fixture': fixture,
                'profile': control['profile'], 'previousProfileOnResume': previous_profile,
                'installationId': control['installationId']}

    @app.get(PREFIX + '/session')
    async def session(headers=Depends(admin)):
        return public_session()

    @app.get(PREFIX + '/runs')
    async def runs(headers=Depends(admin)):
        return {'runs': [{'goldRun': run, 'image': item['package']['manifest']['image'],
                          'sessionId': item['sessionId'], 'packageSha256': item['package']['sha256'],
                          'controlPath': route} for run, (item, _, route) in sorted(catalog.items())]}

    @app.get(PREFIX + '/package')
    async def download(run: str, headers=Depends(admin)):
        if run not in catalog:
            raise HTTPException(404, 'Run không tồn tại')
        selected, _, _ = catalog[run]
        selected_package = Path(selected['package']['path'])
        if sha(selected_package.read_bytes()) != selected['package']['sha256']:
            raise HTTPException(409, 'Gói đã thay đổi; không tiếp tục phiên này')
        return FileResponse(selected_package, media_type='application/octet-stream', filename=run + '.rhe', headers={'Cache-Control': 'no-store'})

    @app.post(PREFIX + '/claim')
    async def claim(body: Claim, headers=Depends(admin)):
        if body.packageSha256 != manifest['package']['sha256']:
            raise HTTPException(409, 'Hash gói không khớp')
        if control['installationId'] not in (None, body.installationId):
            raise HTTPException(409, 'Benchmark đã được một lần cài app khác sử dụng')
        control['installationId'] = body.installationId
        save_control()
        return public_session()

    @app.post(PREFIX + '/profile')
    async def profile(body: ProfileChange, headers=Depends(admin)):
        owner(body)
        if body.profile not in PROFILES:
            raise HTTPException(422, 'Profile không hợp lệ')
        control['profile'] = body.profile
        save_control()
        with (folder / 'profiles.jsonl').open('a', encoding='utf-8') as output:
            output.write(json.dumps({'at': datetime.now(timezone.utc).isoformat(), 'profile': body.profile}) + '\n')
        return {'profile': body.profile, **PROFILES[body.profile]}

    async def observations(headers):
        response = await client.get('/api/reports', params={'limit': 5000}, headers=headers)
        response.raise_for_status()
        reports = [r for r in response.json()['reports'] if str(r.get('description', '')).startswith('Benchmark ' + manifest['sessionId'] + ' ')]
        clusters = await client.get('/api/clusters', headers=headers)
        clusters.raise_for_status()
        return {'reports': reports, 'review': clusters.json().get('review', [])}

    @app.get(PREFIX + '/observations')
    async def observe(headers=Depends(admin)):
        return await observations(headers)

    @app.post(PREFIX + '/feedback/{report_id}')
    async def feedback(report_id: str, body: Owner, headers=Depends(admin)):
        owner(body)
        own = (await observations(headers))['reports']
        report = next((r for r in own if r['id'] == report_id), None)
        if report is None:
            raise HTTPException(404, 'Không phải báo cáo của benchmark này')
        if report.get('status') != 'dispatched':
            response = await client.patch('/api/reports/' + report_id + '/status', headers=headers,
                                          json={'status': 'dispatched', 'statusVersion': report['statusVersion'] + 1})
            response.raise_for_status()
        return {'reportId': report_id, 'status': 'dispatched'}

    @app.post(PREFIX + '/results')
    async def results(body: Results, headers=Depends(admin)):
        owner(body)
        if body.sessionId != manifest['sessionId'] or body.packageSha256 != manifest['package']['sha256']:
            raise HTTPException(409, 'Kết quả không cùng benchmark/gói')
        if len({c.stage for c in body.checks}) != len(body.checks):
            raise HTTPException(422, 'Trùng stage')
        if any(c.stage not in STAGES + ['manual_android_ui', 'manual_physical_network', 'dashboard'] for c in body.checks):
            raise HTTPException(422, 'Stage không hợp lệ')
        def no_secrets(value):
            if isinstance(value, dict):
                if any(re.search(r'password|authorization|(^|_)token$', k, re.I) for k in value):
                    raise HTTPException(422, 'Không lưu mật khẩu/token trong kết quả')
                for v in value.values(): no_secrets(v)
            elif isinstance(value, list):
                for v in value: no_secrets(v)
        record = body.model_dump()
        no_secrets(record)
        verified = await observations(headers)
        record['serverObservations'] = verified
        dashboard_file = folder / 'dashboard-checks.json'
        dashboard = json.loads(dashboard_file.read_text(encoding='utf-8')) if dashboard_file.exists() else None
        if dashboard and body.evidence.get('attemptStartedAtUtc'):
            try:
                started = datetime.fromisoformat(body.evidence['attemptStartedAtUtc'].replace('Z', '+00:00'))
                checked = datetime.fromisoformat(dashboard['atUtc'].replace('Z', '+00:00'))
                if checked < started:
                    dashboard = None
            except (KeyError, ValueError, TypeError, AttributeError):
                dashboard = None
        if dashboard and not {r['id'] for r in verified['reports']}.issubset(set(dashboard.get('mobileReportIds', []))):
            dashboard = None  # New mobile reports require another dashboard verification.
        canonical_checks = [c.model_dump() for c in body.checks if c.stage != 'dashboard']
        for stage in STAGES + ['manual_android_ui', 'manual_physical_network']:
            if not any(c['stage'] == stage for c in canonical_checks):
                canonical_checks.append({'stage': stage, 'status': 'NOT_RUN', 'method': 'coordinator', 'detail': 'App chưa gửi kết quả của bước này'})
        canonical_checks.append({'stage': 'dashboard', 'status': dashboard['status'] if dashboard else 'NOT_RUN',
                                 'method': 'coordinator', 'detail': 'Playwright đối chiếu bài benchmark trên flood-rescue' if dashboard else 'Chưa chạy coordinator dashboard'})
        server_by_id = {r['id']: r for r in verified['reports']}
        for check in canonical_checks:
            if check['status'] != 'PASS' or check['stage'] not in STAGES:
                continue
            stage = check['stage']
            record_id = body.reports.get('online' if stage == 'feedback' else stage)
            report = server_by_id.get(record_id)
            expected_stage = 'online' if stage == 'feedback' else stage
            marker = re.escape(f"Benchmark {manifest['sessionId']} {expected_stage}")
            valid = report is not None and re.fullmatch(marker + r'(?: attempt \d+)?', str(report.get('description', ''))) is not None
            if stage == 'no_gps' and valid:
                valid = report.get('lat') is None and report.get('lng') is None and record_id in verified['review']
            if stage == 'feedback' and valid:
                valid = report.get('status') == 'dispatched'
            if not valid:
                check.update(status='FAIL', method='coordinator', detail='Server không xác nhận được báo cáo/trạng thái của stage')
        record['checks'] = canonical_checks
        counts = Counter(c['status'] for c in canonical_checks)
        record['counts'] = {k: counts[k] for k in ['PASS', 'FAIL', 'NOT_RUN']}
        record['automaticComplete'] = all(any(c['stage'] == s and c['status'] == 'PASS' for c in canonical_checks) for s in STAGES)
        record['status'] = ('failed' if counts['FAIL'] else 'complete' if record['automaticComplete'] and not counts['NOT_RUN']
                            else 'complete_with_gaps' if record['automaticComplete'] else 'in_progress')
        record['recordedAtUtc'] = datetime.now(timezone.utc).isoformat()
        saved_manifest = folder / 'manifest.json'
        snapshot = json.loads(saved_manifest.read_text(encoding='utf-8')) if saved_manifest.exists() else manifest
        if snapshot['sessionId'] != manifest['sessionId'] or snapshot['package']['sha256'] != manifest['package']['sha256']:
            raise HTTPException(409, 'Manifest đã đổi benchmark/gói')
        device = re.sub(r'[^A-Za-z0-9_-]', '_', str(body.environment.get('device', {}).get('model', 'unknown')))[:60]
        destination = (results_root or folder / 'results') / device / manifest['sessionId']
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        atomic_json(destination / 'attempts' / (stamp + '.json'), record)
        atomic_json(destination / (manifest['sessionId'] + '.json'), record)
        import csv
        with (destination / (manifest['sessionId'] + '.csv')).open('w', encoding='utf-8-sig', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=['stage', 'status', 'method', 'detail'])
            writer.writeheader()
            writer.writerows(canonical_checks)
        atomic_json(destination / 'manifest.json', snapshot)
        save_manual_errors(destination, record, fixture['goldRun'], dashboard)
        return {'status': record['status'], 'counts': record['counts'], 'automaticComplete': record['automaticComplete'], 'checks': canonical_checks}

    @app.api_route('/{path:path}', methods=['GET', 'POST', 'PATCH', 'PUT', 'DELETE', 'OPTIONS', 'HEAD'])
    async def proxy(path: str, request: Request):
        # Identity/auth stay reachable; only the data path is deliberately interrupted.
        exempt = path == 'healthz' or path.startswith('api/auth/')
        selected = control['profile']
        profile = PROFILES['online' if exempt else selected]
        if profile.get('blocked'):
            return Response('E2E proxy: data path blocked', status_code=503, headers={'X-E2E-Profile': selected})
        kbps = profile.get('kbps')
        delay = profile.get('rttMs', 0) / 2000
        sent = [0]
        started = time.monotonic()
        async def upload():
            async for chunk in request.stream():
                sent[0] += len(chunk)
                if sent[0] > 20 * 1024 * 1024:
                    raise HTTPException(413, 'Request quá lớn')
                if kbps: await asyncio.sleep(len(chunk) * 8 / (kbps * 1000))
                yield chunk
        if delay: await asyncio.sleep(delay)
        headers = {k: v for k, v in request.headers.items() if k.lower() not in HOP and not k.lower().startswith('x-forwarded-')}
        try:
            upstream = await client.send(client.build_request(request.method, '/' + path,
                                         params=request.query_params, headers=headers, content=upload()), stream=True)
        except httpx.HTTPError:
            return Response('Backend chưa sẵn sàng', status_code=502)
        async def download_stream():
            received = 0
            try:
                if delay: await asyncio.sleep(delay)
                async for chunk in upstream.aiter_bytes(1024):
                    if kbps: await asyncio.sleep(len(chunk) * 8 / (kbps * 1000))
                    received += len(chunk)
                    yield chunk
            finally:
                await upstream.aclose()
                with (folder / 'traffic.jsonl').open('a', encoding='utf-8') as output:
                    output.write(json.dumps({'profile': selected, 'path': path, 'method': request.method,
                                             'bodyBytesUp': sent[0], 'bodyBytesDown': received,
                                             'elapsedS': time.monotonic() - started}) + '\n')
        return StreamingResponse(download_stream(), status_code=upstream.status_code,
                                 headers={k: v for k, v in upstream.headers.items() if k.lower() not in HOP})
    return app
