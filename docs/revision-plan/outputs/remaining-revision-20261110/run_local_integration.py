"""Run existing Linux app integration tests against an isolated local backend."""
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent / 'checks'


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def main():
    with tempfile.TemporaryDirectory(prefix='rescue-revision-e2e-') as tmp:
        env = dict(os.environ, RESCUE_DB_FILE=str(Path(tmp) / 'reports.db'),
                   RESCUE_UPLOADS_DIR=str(Path(tmp) / 'uploads'),
                   RESCUE_ADMIN_USERNAME='revision-test',
                   RESCUE_ADMIN_PASSWORD='local-only-revision-test')
        port, link = free_port(), free_port()
        server_url = f'http://127.0.0.1:{port}'
        with (OUT / 'linux-backend.log').open('w') as server_log:
            server = subprocess.Popen([str(ROOT / 'products/be/.venv/bin/python'), '-m', 'uvicorn',
                                       'main:app', '--host', '127.0.0.1', '--port', str(port)],
                                      cwd=ROOT / 'products/be', env=env,
                                      stdout=server_log, stderr=subprocess.STDOUT)
            try:
                for _ in range(100):
                    if server.poll() is not None:
                        raise RuntimeError('Isolated backend exited')
                    try:
                        urllib.request.urlopen(server_url + '/healthz', timeout=1).close()
                        break
                    except OSError:
                        time.sleep(.1)
                else:
                    raise TimeoutError('Backend did not become ready')
                command = [str(Path('/home/ngthtrong/flutter/bin/flutter')),
                           'test', 'integration_test/system_test.dart', '-d', 'linux',
                           '--dart-define=E2E_BACKEND=' + server_url,
                           f'--dart-define=SERVER_URL=http://127.0.0.1:{link}',
                           '--dart-define=ALLOW_INSECURE_LAN=true',
                           '--dart-define=E2E_ADMIN_USER=revision-test',
                           '--dart-define=E2E_ADMIN_PASSWORD=local-only-revision-test',
                           '--dart-define=E2E_IMAGE=' + str(ROOT / 'products/fe/model/Dataset_Flood/high/flood_4791.jpg'),
                           '--reporter', 'expanded']
                with (OUT / 'linux-integration.log').open('w') as log:
                    result = subprocess.run(command, cwd=ROOT / 'products/fe/app', stdout=log,
                                            stderr=subprocess.STDOUT, timeout=360)
                receipt = {'exit_code': result.returncode, 'command': command,
                           'backend': 'Isolated temporary SQLite/uploads; loopback HTTP only',
                           'scope': 'Linux app repository integration, not Android, physical mobile network or SMS'}
                (OUT / 'linux-integration.json').write_text(json.dumps(receipt, indent=2) + '\n')
                print('Linux app integration exit code:', result.returncode)
                return result.returncode
            finally:
                server.terminate()
                server.wait(timeout=15)


if __name__ == '__main__':
    raise SystemExit(main())
