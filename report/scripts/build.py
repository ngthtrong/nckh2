#!/usr/bin/env python3
"""Compile from report/, with separate output directories and grouped bibliography."""
import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def run(args, env=None):
    subprocess.run(args, cwd=ROOT, env=env, check=True)

def has_package(name):
    tool = shutil.which('kpsewhich')
    return bool(tool and subprocess.run([tool, name], capture_output=True, text=True).stdout.strip())

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('target', choices=['content', 'full', 'smoke', 'bulletin-vi', 'bulletin-en', 'summary-vi', 'summary-en'])
    parser.add_argument('--twoside', action='store_true')
    parser.add_argument('--bibliography', choices=['auto', 'bibtex', 'biblatex'], default='auto')
    args = parser.parse_args()
    if not shutil.which('xelatex'):
        parser.error('XeLaTeX is missing.')
    os.chdir(ROOT)
    if args.target == 'full':
        draft_cmd = [sys.executable, 'scripts/build.py', 'content', '--bibliography', args.bibliography]
        if args.twoside:
            draft_cmd.append('--twoside')
        run(draft_cmd)
        run([sys.executable, 'scripts/check_report.py', '--release', '--build-dir',
             'build/content-twoside' if args.twoside else 'build/content'])
        run([sys.executable, 'scripts/build_evidence.py'])
    out = ROOT / 'build' / (args.target + ('-twoside' if args.twoside else ''))
    out.mkdir(parents=True, exist_ok=True)
    # TeX's \include auxiliaries retain the source path inside output-directory.
    for name in ['chapters', 'chapters/01-foundations', 'chapters/02-data-methods',
                 'chapters/03-system', 'chapters/04-evaluation', 'appendices']:
        (out / name).mkdir(parents=True, exist_ok=True)
    report = args.target in ['content', 'full', 'smoke']
    biber_available = has_package('biblatex.sty') and bool(shutil.which('biber'))
    use_biber = report and (args.bibliography == 'biblatex' or (args.bibliography == 'auto' and biber_available))
    if use_biber and not biber_available:
        parser.error('biblatex + biber are required for --bibliography biblatex.')
    if report and not use_biber and not shutil.which('bibtex'):
        parser.error('BibTeX is missing.')
    source = 'main.tex' if args.target in ['content', 'full'] else (
        'template/typography-smoke.tex' if args.target == 'smoke' else f'deliverables/{args.target}.tex')
    definitions = ('\\def\\FullReport{1}' if args.target == 'full' else '')
    definitions += '\\def\\TwoSidedReport{1}' if args.twoside else ''
    definitions += '\\def\\UseBiblatex{1}' if use_biber else '\\def\\UseBibtex{1}'
    job = args.target
    cmd = ['xelatex', '-interaction=nonstopmode', '-halt-on-error', '-file-line-error',
           f'-output-directory={out.relative_to(ROOT)}', f'-jobname={job}',
           definitions + '\\input{' + source + '}']
    env = os.environ.copy()
    # Also find grouped bbl files in the isolated output directory.
    env['TEXINPUTS'] = str(out) + os.pathsep + env.get('TEXINPUTS', '') + os.pathsep
    env['BIBINPUTS'] = str(ROOT) + os.pathsep + env.get('BIBINPUTS', '') + os.pathsep
    backend = 'biblatex' if use_biber else 'bibtex'
    marker = out / '.bibliography-backend'
    previous_aux = out / f'{job}.aux'
    incompatible_aux = previous_aux.exists() and ('\\abx@aux' in previous_aux.read_text(errors='replace')) != use_biber
    if incompatible_aux or (marker.exists() and marker.read_text().strip() != backend):
        for pattern in ['*.aux', '*.bbl', '*.blg', '*.bcf', '*.run.xml', '*.toc', '*.lof', '*.lot', '*.out']:
            for artifact in out.rglob(pattern):
                artifact.unlink()
    marker.write_text(backend + '\n')
    print(f'Building {args.target}: {"biblatex/biber" if use_biber else "BibTeX/natbib"}', flush=True)
    run(cmd, env)
    if report:
        if use_biber:
            run(['biber', '--input-directory', str(out), '--output-directory', str(out), job], env)
        else:
            for group in ['legal', 'books', 'articles']:
                aux = out / f'{job}-{group}.aux'
                databases = re.search(r'\\bibdata\{([^}]+)\}', aux.read_text()).group(1).split(',')
                if any(re.search(r'@\s*(?!comment\b|preamble\b|string\b)\w+\s*[{(]',
                                 (ROOT / (db + '.bib')).read_text(), re.I) for db in databases):
                    run(['bibtex', str(aux.relative_to(ROOT).with_suffix(''))], env)
                else:
                    aux.with_suffix('.bbl').unlink(missing_ok=True)
    run(cmd, env)
    run(cmd, env)
    # Resolve longer TOC/float changes until stable, at most three further passes.
    for _ in range(3):
        log = (out / f'{job}.log').read_text(errors='replace')
        if not any(s in log for s in ['Rerun to get', 'Label(s) may have changed', 'Please rerun LaTeX']):
            break
        run(cmd, env)
    log = (out / f'{job}.log').read_text(errors='replace')
    if any(s in log for s in ['There were undefined references', 'There were undefined citations',
                              'Rerun to get', 'Label(s) may have changed', 'Please rerun LaTeX']):
        raise SystemExit('Unresolved references or pagination; inspect ' + str(out / f'{job}.log'))
    if args.target == 'full':
        run([sys.executable, 'scripts/check_report.py', '--release', '--build-dir', str(out.relative_to(ROOT))])
    print('PDF: ' + str((out / f'{job}.pdf').relative_to(ROOT)))

if __name__ == '__main__':
    try:
        main()
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)
