"""Execute one explicit authorized step with immutable command/exit receipts."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import subprocess
import time

from common import BASE, OUT, PROTOCOL, ROOT, digest, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('name')
    parser.add_argument('--timeout', type=int, default=3600)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command:
        raise SystemExit('Explicit command required')
    receipts = OUT / 'commands'
    receipts.mkdir(exist_ok=True)
    receipt_path = receipts / (args.name + '.json')
    started_path = receipts / (args.name + '-start.json')
    if receipt_path.exists() or started_path.exists():
        raise SystemExit('Receipt exists; choose an explicitly different step name')
    started = time.monotonic()
    receipt = {'command': command, 'cwd': str(ROOT), 'timeout_seconds': args.timeout,
               'start_utc': datetime.now(timezone.utc).isoformat(), 'status': 'RUNNING',
               'input_source_hashes': {str(p.relative_to(ROOT)): digest(p) for p in sorted(BASE.glob('*.py'))},
               'protocol_sha256': digest(PROTOCOL)}
    log_path = OUT / (args.name + '.log')
    with log_path.open('w') as log:
        process = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        receipt['pid'] = process.pid
        write_json(started_path, receipt)
        print(f'START {args.name}: pid={process.pid}', flush=True)
        while process.poll() is None:
            if time.monotonic() - started > args.timeout:
                print('Hard timeout reached; terminating this step', flush=True)
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                receipt['timeout_reached'] = True
                break
            time.sleep(1)
    receipt.update(status='FINISHED', exit_code=process.returncode,
                   elapsed_seconds=time.monotonic() - started,
                   end_utc=datetime.now(timezone.utc).isoformat(), log_sha256=digest(log_path))
    write_json(receipt_path, receipt)
    print(f'END {args.name}: exit={process.returncode}', flush=True)
    print(log_path.read_text()[-4000:], flush=True)
    raise SystemExit(process.returncode if process.returncode is not None else 1)


if __name__ == '__main__':
    main()
