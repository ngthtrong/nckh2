#!/usr/bin/env python3
"""Compare released tweet IDs, using hash-checked snapshots from both rounds."""
import argparse
import csv
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference-cache', type=Path,
                        default=Path('/tmp/nckh2-dataset-search-20261029'))
    parser.add_argument('--cache', type=Path,
                        default=Path('/tmp/nckh2-dataset-search-round2-20261029'))
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location('round1_audit', ROOT.parent / 'scripts/audit_sources.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    references = [('D01', 'humaid_set1.tar.gz', module.profile_humaid),
                  ('D02', 'trecis_train.json.gz', module.profile_trec),
                  ('D06', 'idrisi_harvey_train.jsonl', module.profile_idrisi)]
    old_manifest = json.loads((ROOT.parent / 'audit/sources.json').read_text())
    new_manifest = json.loads((ROOT / 'sources.json').read_text())
    old, fingerprints = {}, {}
    for sid, filename, function in references:
        expected = next(m['sha256'] for m in old_manifest if m['file'] == filename)
        assert module.sha256(args.reference_cache / filename) == expected, filename
        old[sid] = {str(i) for i in function(args.reference_cache / filename)[2]}
        fingerprints[filename] = expected
    for filename in ['quatred.json', 'french.csv']:
        expected = next(m['sha256'] for m in new_manifest if m['file'] == filename)
        assert module.sha256(args.cache / filename) == expected, filename
        fingerprints[filename] = expected
    with (args.cache / 'french.csv').open(encoding='utf-8-sig') as handle:
        french = {r['tweetID'] for r in csv.DictReader(handle)}
    new = {'A03': {r['tweetId'] for r in json.loads((args.cache / 'quatred.json').read_text())},
           'A05': french}
    result = {'status': 'PASS', 'unit': 'distinct original tweet ID',
              'scope': 'Only the five explicitly hash-checked snapshots; zero matches is not proof of full corpus independence',
              'comparisons': {sid: {'unique_ids': len(ids),
                                   'overlap_with_round1': {ref: len(ids & refids) for ref, refids in old.items()}}
                              for sid, ids in new.items()},
              'source_hashes': fingerprints}
    (ROOT / 'audit/cross-corpus-overlap.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result['comparisons']))


if __name__ == '__main__':
    main()
