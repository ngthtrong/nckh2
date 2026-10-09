#!/usr/bin/env python3
"""Build the standalone template with an empty or populated IEEE bibliography."""
import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
TARGETS = ['content', 'smoke', 'bulletin-vi', 'bulletin-en', 'summary-vi', 'summary-en']
UNRESOLVED = re.compile(
    r'undefined references|undefined citations|(?:Reference|Citation).*undefined|'
    r'Rerun to get|Label\(s\) may have changed|Please (?:re)?run (?:LaTeX|Biber)|'
    r'Please rerun LaTeX', re.I)
LAYOUT_ERRORS = re.compile(
    r'Overfull \\[hv]box|multiply[ -]defined|destination with the same identifier|'
    r'Font shape .*undefined|Missing character:|LaTeX Error|Package \S+ Error', re.I)


def has_package(name):
    return bool(shutil.which('kpsewhich') and subprocess.run(
        ['kpsewhich', name], capture_output=True, text=True).stdout.strip())


def run(command, env):
    result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True)
    if result.returncode:
        print(result.stdout[-10000:] + result.stderr[-3000:], file=sys.stderr)
        raise SystemExit(result.returncode)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('target', choices=TARGETS)
    parser.add_argument('--twoside', action='store_true')
    parser.add_argument('--bibliography', choices=['auto', 'bibtex', 'biblatex'], default='auto')
    args = parser.parse_args()
    if not shutil.which('xelatex'):
        parser.error('XeLaTeX is missing; run make doctor.')
    bibliography = args.target in ['content', 'smoke']
    biber_available = has_package('ieee.bbx') and bool(shutil.which('biber'))
    use_biber = bibliography and (args.bibliography == 'biblatex' or
                                  (args.bibliography == 'auto' and biber_available))
    if use_biber and not biber_available:
        parser.error('biblatex-ieee and biber are required for biblatex.')
    if bibliography and not use_biber and not shutil.which('bibtex'):
        parser.error('BibTeX is missing.')
    name = args.target + ('-twoside' if args.twoside else '')
    out = ROOT / 'build' / name
    out.mkdir(parents=True, exist_ok=True)
    for source in (ROOT / 'chapters').rglob('*.tex'):
        (out / source.relative_to(ROOT).parent).mkdir(parents=True, exist_ok=True)
    (out / 'appendices').mkdir(exist_ok=True)
    # Drop old auxiliary state: citation removal/backend switches cannot leak old entries.
    for pattern in ['*.aux', '*.bbl', '*.blg', '*.bcf', '*.run.xml', '*.toc', '*.lof', '*.lot', '*.out']:
        for artifact in out.rglob(pattern):
            artifact.unlink()
    source = ('main.tex' if args.target == 'content' else 'examples/formatting.tex'
              if args.target == 'smoke' else f'deliverables/{args.target}.tex')
    definitions = ('\\def\\TwoSidedReport{1}' if args.twoside else '')
    definitions += '\\def\\UseBiblatex{1}' if use_biber else '\\def\\UseBibtex{1}'
    env = os.environ.copy()
    env['TEXINPUTS'] = str(out) + os.pathsep + env.get('TEXINPUTS', '') + os.pathsep
    env['BIBINPUTS'] = str(ROOT) + os.pathsep + env.get('BIBINPUTS', '') + os.pathsep

    def latex():
        run(['xelatex', '-interaction=nonstopmode', '-halt-on-error', '-file-line-error',
             f'-output-directory={out.relative_to(ROOT)}', f'-jobname={args.target}',
             definitions + '\\input{' + source + '}'], env)

    print(f'Building {name} ({"biblatex/IEEE" if use_biber else "BibTeX/IEEE"})', flush=True)
    latex()
    aux = '\n'.join(p.read_text(errors='replace') for p in out.rglob('*.aux'))
    cited = bibliography and bool(re.search(r'\\(?:abx@aux@cite|abx@aux@nocite|citation)\{', aux))
    if cited:
        definitions += '\\def\\TemplateHasReferences{1}'
        # In the BibTeX branch, this writes bibdata into the aux before bibtex runs.
        latex()
    if use_biber:
        # Biber also creates a valid empty bbl, avoiding endless rerun warnings.
        run(['biber', '--input-directory', str(out), '--output-directory', str(out), args.target], env)
    elif cited:
        run(['bibtex', str((out / args.target).relative_to(ROOT))], env)
    for iteration in range(6):
        latex()
        log = (out / f'{args.target}.log').read_text(errors='replace')
        if iteration >= 1 and not UNRESOLVED.search(log):
            break
    log = (out / f'{args.target}.log').read_text(errors='replace')
    if UNRESOLVED.search(log) or LAYOUT_ERRORS.search(log):
        lines = [line for line in log.splitlines() if UNRESOLVED.search(line) or LAYOUT_ERRORS.search(line)]
        raise SystemExit('PDF validation failed:\n' + '\n'.join(lines) + f'\nSee {out}')
    print(f'PDF: {(out / (args.target + ".pdf")).relative_to(ROOT)}; '
          f'{"references resolved" if cited else "no references to process"}')


if __name__ == '__main__':
    main()
