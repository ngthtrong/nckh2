"""Fail-closed intake gate for independently annotated Vietnamese rescue pairs."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


def validate(records_path: Path, annotations_path: Path, target_approval: Path | None):
    with records_path.open(newline='') as f:
        records = list(csv.DictReader(f))
    with annotations_path.open(newline='') as f:
        annotations = list(csv.DictReader(f))
    issues = []
    approval = {}
    if not records:
        issues.append('NO_REAL_PAIRED_RECORDS')
    if not annotations:
        issues.append('NO_INDEPENDENT_ANNOTATIONS')
    if target_approval is not None and target_approval.is_file():
        try:
            approval = json.loads(target_approval.read_text())
        except (ValueError, TypeError):
            issues.append('INVALID_TARGET_APPROVAL_JSON')
    if (approval.get('status') != 'APPROVED_BY_RESPONSIBLE_HUMAN'
            or not all(approval.get(k) for k in ['task', 'labels', 'approved_by', 'expert_ref', 'guideline_ref'])):
        issues.append('NO_TARGET_AND_EXPERT_APPROVAL')
    required = ['report_id', 'event_id', 'source_id', 'source_url', 'usage_basis', 'language', 'text',
                'image_path', 'image_sha256', 'privacy_review_ref']
    ids = set()
    for row in records:
        rid = row.get('report_id', '')
        if not rid or rid in ids:
            issues.append(f'EMPTY_OR_DUPLICATE_ID:{rid}')
        ids.add(rid)
        for field in required:
            if not row.get(field, '').strip():
                issues.append(f'MISSING_{field}:{rid}')
        if row.get('language') != 'vi':
            issues.append(f'NOT_VI:{rid}')
        image = Path(row.get('image_path', ''))
        if not image.is_absolute():
            image = records_path.parent / image
        if not image.is_file():
            issues.append(f'MISSING_IMAGE:{rid}')
        elif hashlib.sha256(image.read_bytes()).hexdigest() != row.get('image_sha256'):
            issues.append(f'IMAGE_HASH_MISMATCH:{rid}')
        votes = [a for a in annotations if a.get('report_id') == rid]
        independent = {a.get('annotator_id') for a in votes if a.get('stage') == 'independent' and a.get('annotator_id')}
        adjudicated = [a for a in votes if a.get('stage') == 'adjudicated' and a.get('label') and a.get('evidence_ref')]
        if len(independent) < 2:
            issues.append(f'FEWER_THAN_TWO_ANNOTATORS:{rid}')
        if not adjudicated:
            issues.append(f'NO_ADJUDICATED_LABEL:{rid}')
        if any(a.get('label_origin') != 'human' for a in votes):
            issues.append(f'NON_HUMAN_OR_UNDECLARED_LABEL:{rid}')
        if approval.get('labels') and any(a.get('label') not in approval['labels'] for a in votes):
            issues.append(f'LABEL_OUTSIDE_APPROVED_SCHEMA:{rid}')
    if any(a.get('report_id') not in ids for a in annotations):
        issues.append('ORPHAN_ANNOTATION')
    return {'status': 'NO_GO' if issues else 'GO_PROTOCOL_REVIEW', 'records': len(records),
            'annotations': len(annotations), 'issues': issues,
            'limits': 'Passing is structural intake only, not label validity, adequate sample size, IAA or operational approval'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--records', type=Path, required=True)
    parser.add_argument('--annotations', type=Path, required=True)
    parser.add_argument('--target-approval', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = validate(args.records, args.annotations, args.target_approval)
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.write_text(rendered)
    print(rendered)
    raise SystemExit(2 if result['status'] == 'NO_GO' else 0)


if __name__ == '__main__':
    main()
