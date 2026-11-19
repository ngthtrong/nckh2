"""Export verified software evidence; do not execute app/device tests in a build."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'docs/revision-plan/outputs/remaining-revision-20261110'


def main():
    evidence = json.loads((SOURCE / 'software-evidence.json').read_text())
    if evidence['status'] != 'VERIFIED_SOFTWARE_REGRESSION_ONLY':
        raise ValueError('Missing software regression evidence')
    for relative, expected in evidence['source_sha256'].items():
        if hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() != expected:
            raise ValueError('Software changed since verification: ' + relative)
    for name, expected in evidence['log_sha256'].items():
        if hashlib.sha256((SOURCE / 'checks' / name).read_bytes()).hexdigest() != expected:
            raise ValueError('Verification log changed: ' + name)
    values = {'FlutterPass': 'flutter_pass', 'FlutterSkipped': 'flutter_skipped',
              'BackendPass': 'backend_pass', 'TargetedPass': 'targeted_after_pass',
              'LinuxPass': 'linux_integration_pass', 'GraphTests': 'graph_regression_tests'}
    output = [r'% Generated from saved software receipts; no device test run during build.']
    output += [r'\providecommand{\Software' + suffix + '}{' + str(evidence[key]) + '}'
               for suffix, key in values.items()]
    (ROOT / 'report/generated/software-revision-values.tex').write_text('\n'.join(output) + '\n')
    print('Verified saved software evidence: Flutter, backend, graph and Linux integration')


if __name__ == '__main__':
    main()
