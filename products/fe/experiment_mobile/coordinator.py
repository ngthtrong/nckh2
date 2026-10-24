"""Benchmark mobile dùng backend/dashboard flood-rescue hiện có và proxy thử mạng."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone, timedelta
import getpass
import ipaddress
import json
import os
from pathlib import Path
import shutil
import re
import socket
import subprocess
import sys
import time
from types import SimpleNamespace

import httpx
import uvicorn

from build_package import HERE, ROOT, web
from prepare_assets import benchmark_package, verify_assets
from mobile_api import atomic_json, create_app

VIETNAM = timezone(timedelta(hours=7))


def benchmark_name(label, now=None):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,39}', label):
        raise ValueError('Tên benchmark cần 1..40 chữ không dấu, số, dấu _ hoặc -')
    return (now or datetime.now(timezone.utc)).astimezone(VIETNAM).strftime('%Y-%m-%d_%H-%M-%S-%f_') + label


def session_folder(name):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', name):
        raise ValueError('Tên benchmark không hợp lệ')
    return HERE / 'benchmarks' / name


def load_session(name=None):
    if name is None:
        latest = HERE / 'benchmarks/latest.json'
        if not latest.is_file():
            raise ValueError('Chưa có benchmark; chạy start trước')
        name = json.loads(latest.read_text(encoding='utf-8'))['benchmark']
    folder = session_folder(name)
    data = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
    if data.get('backendMode') != 'shared' or data['sessionId'] != name:
        raise ValueError('Hãy tạo benchmark mới dùng flood-rescue; không dùng lại phiên Docker riêng')
    return folder, data


def selected_session(options):
    folder, manifest = load_session(options.benchmark)
    run = getattr(options, 'run', None)
    if run is not None and run != manifest['seedRun']:
        other_name = manifest['sessionId'][:71] + f'_run_{run:03d}'
        other_folder, other = load_session(other_name)
        if other.get('serverId') != manifest.get('serverId') or other['upstream'] != manifest['upstream']:
            raise ValueError('Run không cùng backend/DB')
        return other_folder, other
    return folder, manifest


def verify_backend(manifest, *, password=None):
    deadline = time.monotonic() + 120
    while True:
        try:
            response = httpx.get(manifest['upstream'] + '/healthz', timeout=4)
            response.raise_for_status()
            health = response.json()
            break
        except (httpx.HTTPError, ValueError):
            if time.monotonic() >= deadline:
                raise RuntimeError('Backend chưa sẵn sàng sau 120 giây')
            time.sleep(2)
    server_id = health.get('serverId') if isinstance(health, dict) else None
    if not isinstance(server_id, str) or not server_id.strip():
        raise RuntimeError('Backend flood-rescue đang cũ hoặc không tương thích (healthz thiếu serverId). '
                           'Tại gốc repo chạy: docker compose up -d --build be dashboard; rồi chạy lại benchmark. '
                           'Giữ volume dữ liệu hiện có, không dùng down -v.')
    if manifest.get('serverId') not in (None, server_id):
        raise RuntimeError('DB/serverId đã đổi; không resume trên DB khác')
    manifest['serverId'] = server_id
    if password is not None:
        with httpx.Client(base_url=manifest['upstream'], timeout=60) as client:
            login = client.post('/api/auth/login', json={'username': manifest['adminUsername'], 'password': password})
            login.raise_for_status()
            token = login.json()['token']
            try:
                identity = client.get('/api/auth/me', headers={'Authorization': 'Bearer ' + token})
                identity.raise_for_status()
                if identity.json().get('role') != 'admin':
                    raise RuntimeError('Cần tài khoản admin của flood-rescue để chạy benchmark')
            finally:
                client.post('/api/auth/logout', headers={'Authorization': 'Bearer ' + token})


def serve(manifest, folder):
    verify_backend(manifest)
    alternatives = []
    configured = {item['goldRun']: item for item in verify_assets()['runs']}
    for run in sorted(configured):
        if run == manifest['package']['manifest']['goldRun']:
            continue
        name = manifest['sessionId'][:71] + '_' + run
        other_folder = session_folder(name)
        saved = other_folder / 'manifest.json'
        if saved.exists():
            other = json.loads(saved.read_text(encoding='utf-8'))
            if other.get('serverId') != manifest.get('serverId') or other['upstream'] != manifest['upstream']:
                raise ValueError('Benchmark run khác không cùng backend/DB')
        else:
            info = benchmark_package(int(run.removeprefix('run_')), other_folder / 'package.rhe')
            other = dict(manifest, sessionId=name, seedRun=int(run.removeprefix('run_')), package=info)
            atomic_json(saved, other)
        alternatives.append((other, other_folder))
    print(f"\nBenchmark: {manifest['sessionId']}\nRun: run_{manifest['seedRun']:03d}")
    print(f"SERVER_URL cho app: {manifest['appUrl']}\nDashboard trên máy tính: {manifest['dashboardUrl']}")
    print('Giữ cửa sổ này mở. Ctrl+C dừng benchmark proxy; Docker flood-rescue vẫn chạy.')
    uvicorn.run(create_app(manifest, folder, results_root=HERE / 'results', run_manifests=alternatives), host='0.0.0.0',
                port=manifest['proxyPort'], access_log=True)


def start(options):
    address = ipaddress.ip_address(options.lan_ip)
    if address.version != 4 or not address.is_private or address.is_loopback:
        raise ValueError('--lan-ip cần IPv4 LAN của máy tính, ví dụ 192.168.1.73')
    ports = [options.backend_port, options.dashboard_port, options.proxy_port]
    if len(set(ports)) != 3 or any(not 1024 <= p <= 65535 for p in ports):
        raise ValueError('Ba cổng phải khác nhau, trong 1024..65535')
    # Backend/dashboard are already running; only the proxy needs a free port.
    with socket.socket() as probe:
        probe.bind(('0.0.0.0', options.proxy_port))
    session_id = benchmark_name(options.benchmark or f'mobile_run_{options.seed_run:03d}')
    folder = session_folder(session_id)
    folder.mkdir(parents=True, exist_ok=False)
    info = benchmark_package(options.seed_run, folder / 'package.rhe')
    manifest = dict(sessionId=session_id, backendMode='shared', seedRun=options.seed_run,
                    createdAtUtc=datetime.now(timezone.utc).isoformat(),
                    package=info, adminUsername=options.username,
                    backendPort=options.backend_port, dashboardPort=options.dashboard_port, proxyPort=options.proxy_port,
                    upstream=f'http://127.0.0.1:{options.backend_port}',
                    appUrl=f'http://{options.lan_ip}:{options.proxy_port}',
                    dashboardUrl=f'http://127.0.0.1:{options.dashboard_port}')
    password = os.environ.get('RESCUE_ADMIN_PASSWORD') or getpass.getpass('Mật khẩu admin hiện có của flood-rescue: ')
    verify_backend(manifest, password=password)
    atomic_json(folder / 'manifest.json', manifest)
    atomic_json(HERE / 'benchmarks/latest.json', {'benchmark': session_id})
    serve(manifest, folder)


def build_apk(options):
    # Compatibility only: a normal Flutter build consumes the same prepared assets.
    verify_assets()
    raise RuntimeError('Build APK ngay tại products/fe/app: flutter build apk --flavor admin --release '
                       '--dart-define=ALLOW_INSECURE_LAN=true --dart-define=SERVER_URL=http://IP_MAY_TINH:18101. '
                       'Không cần tạo benchmark trước khi build.')


def dashboard_mobile_targets(session_id, reports):
    targets = [r['id'] for r in reports if str(r.get('description', '')).startswith(f'Benchmark {session_id} ')]
    if not targets:
        raise ValueError('Chưa có báo cáo điện thoại của benchmark; chạy online trên app trước')
    return targets


def dashboard(options):
    folder, manifest = selected_session(options)
    verify_backend(manifest)
    password = os.environ.get('RESCUE_ADMIN_PASSWORD') or getpass.getpass('Mật khẩu admin hiện có của flood-rescue: ')
    web.args = SimpleNamespace(api=manifest['upstream'], dashboard=manifest['dashboardUrl'], username=manifest['adminUsername'],
                               password=password, upload_dir=str(folder), screenshots=str(folder / 'dashboard-screenshots'))
    web.results = []
    atomic_json(folder / 'dashboard-checks.json', {'status': 'NOT_RUN', 'checks': [], 'mobileReportIds': [],
                                                'atUtc': datetime.now(timezone.utc).isoformat()})
    targets = dashboard_mobile_targets(manifest['sessionId'], web.api('/api/reports?limit=5000')['reports'])
    (folder / 'dashboard-screenshots').mkdir(exist_ok=True)
    from playwright.sync_api import sync_playwright
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=not options.headed)
            try:
                # Shared DB: only inspect the benchmark reports; never dispatch unrelated clusters.
                page = browser.new_page(viewport={'width': 1400, 'height': 1000})
                page.goto(manifest['dashboardUrl'], wait_until='networkidle')
                page.fill('#login-username', manifest['adminUsername'])
                page.fill('#login-password', password)
                page.click('#login-form button[type=submit]')
                page.wait_for_selector('#report-rows tr')
                for report_id in targets:
                    page.fill('#f-q', report_id)
                    row = page.locator('#report-rows [data-open="' + report_id + '"]')
                    row.wait_for(state='visible', timeout=15000)
                    row.click()
                    page.wait_for_selector('#drawer:not([hidden])')
                    detail = json.loads(page.text_content('#d-raw'))
                    web.check(detail.get('id') == report_id and str(detail.get('description', '')).startswith(f"Benchmark {manifest['sessionId']} "),
                              'Dashboard hiển thị đúng bài Android: ' + report_id)
                    page.screenshot(path=str(folder / 'dashboard-screenshots' / (report_id + '.png')))
                    page.click('#drawer-close')
                page.close()
            finally:
                browser.close()
    except Exception as exc:
        # Preserve an attempted dashboard failure instead of leaving NOT_RUN forever.
        detail = str(exc).replace(password, '[đã ẩn]')[:1600]
        web.results.append(('FAIL', f'Kiểm tra dashboard không hoàn tất ({type(exc).__name__}): {detail}'))
    record = {'checks': [{'status': status, 'detail': label} for status, label in web.results],
              'atUtc': datetime.now(timezone.utc).isoformat(), 'mobileReportIds': targets}
    record['status'] = 'PASS' if record['checks'] and all(c['status'] == 'PASS' for c in record['checks']) else 'FAIL'
    atomic_json(folder / 'dashboard-checks.json', record)
    print('Dashboard:', record['status'], '(xuất lại kết quả từ app để tổng hợp)')


def collect(options):
    folder, manifest = selected_session(options)
    sdk_adb = Path(os.environ.get('LOCALAPPDATA', '')) / 'Android/Sdk/platform-tools/adb.exe'
    adb = options.adb or shutil.which('adb') or (str(sdk_adb) if sdk_adb.is_file() else None)
    if not adb:
        raise RuntimeError('Thêm Android platform-tools vào PATH hoặc truyền --adb đường_dẫn_adb.exe')
    command = [adb, '-s', options.device]
    destination = folder / 'device-evidence' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    destination.mkdir(parents=True)
    for name, arguments in [('device.txt', ['shell', 'getprop']), ('logcat.txt', ['logcat', '-d', '-v', 'threadtime'])]:
        with (destination / name).open('wb') as output:
            subprocess.run(command + arguments, stdout=output, check=True)
    subprocess.run(command + ['shell', 'screencap', '-p', '/sdcard/mobile-e2e.png'], check=True)
    subprocess.run(command + ['pull', '/sdcard/mobile-e2e.png', str(destination / 'screen.png')], check=True)
    print('Bằng chứng:', destination)


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    new = commands.add_parser('start')
    new.add_argument('--seed-run', type=int, choices=(1, 2), default=1)
    new.add_argument('--lan-ip', required=True)
    new.add_argument('--backend-port', type=int, default=8000)
    new.add_argument('--dashboard-port', type=int, default=8080)
    new.add_argument('--proxy-port', type=int, default=18101)
    new.add_argument('--username', default='admin')
    new.add_argument('--benchmark', help='Tên benchmark, ví dụ mobile_run_001; tự thêm ngày giờ')
    for name in ['resume', 'stop', 'build-apk', 'dashboard', 'collect']:
        item = commands.add_parser(name)
        item.add_argument('--benchmark', help='Tên đầy đủ của lượt cũ; mặc định lấy lượt gần nhất')
        if name in ('dashboard', 'collect'):
            item.add_argument('--run', type=int, choices=(1, 2), help='Chọn run của lượt benchmark')
        if name == 'dashboard': item.add_argument('--headed', action='store_true')
        if name == 'collect':
            item.add_argument('--device', required=True)
            item.add_argument('--adb')
    options = parser.parse_args()
    if options.command == 'start': return start(options)
    if options.command == 'build-apk': return build_apk(options)
    if options.command == 'dashboard': return dashboard(options)
    if options.command == 'collect': return collect(options)
    folder, manifest = load_session(options.benchmark)
    if options.command == 'resume':
        password = os.environ.get('RESCUE_ADMIN_PASSWORD') or getpass.getpass('Mật khẩu admin hiện có của flood-rescue: ')
        verify_backend(manifest, password=password)
        return serve(manifest, folder)
    print('Trong cửa sổ đang chạy benchmark, nhấn Ctrl+C để dừng proxy. Docker flood-rescue giữ nguyên.')


if __name__ == '__main__':
    main()
