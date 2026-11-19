"""Freeze current source/PDF/evidence after scientific and report checks finish."""
from __future__ import annotations

import re
import subprocess
import difflib

from common import BASE, OUT, ROOT, digest, read_json, write_json


def main():
    checks = {}
    expected = {'build-layout-final': 0, 'report-check-layout-final': 0, 'report-check-twoside-layout-final': 0,
                'contracts-final': 0, 'verify': 0, 'verify-effects': 0, 'inference-smoke': 0,
                'preservation': 0, 'inspect-report-layout-final': 0, 'vi-intake-final': 2}
    for name, code in expected.items():
        checks['command_' + name] = read_json(OUT / 'commands' / (name + '.json'))['exit_code'] == code
    verification = read_json(OUT / 'verification.json')
    checks['public_pilot_verification'] = verification['status'] == 'PASS_PUBLIC_PILOT'
    checks['result_hashes_current'] = all(digest(ROOT / p) == h for p, h in verification['result_hashes'].items())
    checks['fitted_model_current'] = digest(BASE / 'models/classifiers.joblib') == read_json(OUT / 'training.json')['model_sha256']
    checks['encoder_current'] = digest(BASE / 'cache/torch/checkpoints/mobilenet_v3_small-047dcff4.pth') == read_json(OUT / 'features.json')['checkpoint_sha256']
    checks['effects_replay'] = read_json(OUT / 'effects-verification.json')['status'] == 'PASS'
    checks['local_inference_smoke'] = read_json(OUT / 'inference-smoke.json')['status'] == 'PASS'
    checks['vi_gate_kept_no_go'] = read_json(OUT / 'vi-intake.json')['status'] == 'NO_GO'
    checks['old_files_preserved'] = read_json(OUT / 'preservation.json')['status'] == 'PASS'
    inspections = read_json(OUT / 'report-checks/pdf-inspection.json')
    pdf_keys = ['content', 'content-twoside', 'bulletin-vi', 'bulletin-en', 'summary-vi', 'summary-en']
    checks['pdf_hashes_current'] = all(digest(ROOT / inspections[k]['pdf']) == inspections[k]['sha256'] for k in pdf_keys)
    checks['all_fonts_embedded'] = all(inspections[k]['fonts_embedded'] for k in pdf_keys)
    checks['main_pdf_alias'] = digest(ROOT / 'report/main.pdf') == inspections['content']['sha256']
    checks['diff_whitespace'] = subprocess.run(['git', 'diff', '--check'], cwd=ROOT, capture_output=True).returncode == 0
    documents = [ROOT / 'docs/revision-plan' / p for p in ['README.md', '04-phase-roadmap.md', '05-traceability-matrix.md', 'multimodal-extension.md']]
    skipped = {'before', 'report-checks-first', 'report-checks-before-summary-trim', '__pycache__'}
    documents += [BASE / 'README.md'] + [p for p in OUT.rglob('*.md') if not (set(p.parts) & skipped)]
    broken = []
    for document in documents:
        for link in re.findall(r'\]\(([^)]+)\)', document.read_text()):
            if '://' in link or link.startswith('#'):
                continue
            if not (document.parent / link.split('#')[0]).exists():
                broken.append([str(document.relative_to(ROOT)), link])
    checks['active_document_links'] = not broken
    for key, value in checks.items():
        print(key, value, flush=True)
    status = 'COMPLETE_PUBLIC_BENCHMARK_AND_ANNOTATION_KIT' if all(checks.values()) else 'INCOMPLETE_CHECKS'
    write_json(OUT / 'final-validation.json', {'status': status, 'checks': checks, 'broken_links': broken,
              'phase_scope': 'P09-P14 public benchmark plus empty Vietnamese annotation kit; not complete Vietnamese rescue modeling',
              'phase_status': {'P09': 'DONE_PUBLIC_PROTOCOL', 'P10': 'DONE_PUBLIC_INTAKE_VI_KIT_EMPTY',
                               'P11': 'DONE_PUBLIC_EN_BASELINES', 'P12': 'DONE_PUBLIC_ABLATION',
                               'P13': 'PARTIAL_LOCAL_CLI_ONLY', 'P14': 'DONE_SCOPED_REPORT_VALIDATION'},
              'review_status': {'B1': 'PARTIAL', 'B3': 'PARTIAL', 'B4': 'PARTIAL', 'B5': 'PARTIAL_PUBLIC_ABLATION_EXECUTED'},
              'pdf_pages': {k: inspections[k]['pages'] for k in pdf_keys}, 'release_approval': False,
              'open': ['Vietnamese paired data, independent annotations and expert target approval',
                       'application urgency integration and Android/E2E evaluation',
                       'original image provenance, RQ2 eight discrepancies and other historical evidence gaps']})
    (OUT / 'git-status-after.txt').write_text(subprocess.check_output(['git', 'status', '--short'], cwd=ROOT, text=True))
    patch = []
    before = OUT / 'before'
    for old in sorted(before.rglob('*')):
        if old.is_file():
            relative = str(old.relative_to(before))
            patch.extend(difflib.unified_diff(old.read_text().splitlines(True), (ROOT / relative).read_text().splitlines(True),
                                              fromfile='a/' + relative, tofile='b/' + relative))
    (OUT / 'session-source-diff.patch').write_text(''.join(patch))
    paths = [p for p in BASE.iterdir() if p.is_file()]
    paths += [p for p in OUT.rglob('*') if p.is_file() and p.suffix not in {'.png', '.log'}
              and not (set(p.parts) & skipped)
              and p.name not in {'baseline-files.json', 'final-hashes.json'}]
    paths += [ROOT / 'report/main.pdf'] + [ROOT / inspections[k]['pdf'] for k in pdf_keys]
    paths += [p for p in (ROOT / 'report').rglob('*') if p.is_file() and 'build' not in p.parts and '__pycache__' not in p.parts
              and (p.suffix in {'.tex', '.bib', '.py', '.json'} or p.name in {'Makefile', 'RULES.md'})]
    paths += documents
    write_json(OUT / 'final-hashes.json', {str(p.relative_to(ROOT)): digest(p) for p in sorted(set(paths))})
    if not all(checks.values()):
        raise SystemExit(1)
    print(status, flush=True)


if __name__ == '__main__':
    main()
