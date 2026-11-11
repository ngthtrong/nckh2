#!/usr/bin/env python3
"""Generate the content-only English-then-Vietnamese script and slide notes."""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def write_notes():
    content=json.loads((ROOT/'research/talk-track.json').read_text())
    revision=json.loads((ROOT/'research/revision-content.json').read_text())
    index=json.loads((ROOT/'slide-index.json').read_text())
    titles={row['slide']:row['title'] for row in index}
    if [row['slide'] for row in content] != list(range(1,27)):
        raise ValueError('Expected 26 ordered bilingual talk-track entries')
    notes=[]
    for row,original in zip(content,revision['order']):
        english=row['english'].strip();vietnamese=row['vietnamese'].strip()
        if not english or not vietnamese:
            raise ValueError(f"Missing language for slide {row['slide']}")
        if re.search(r'\[\d+(?:[–,\-]\d+)*\]|https?://|Source notes:|Suggested time:',english+'\n'+vietnamese):
            raise ValueError(f"Non-spoken citation or metadata on slide {row['slide']}")
        notes.append({'slide':row['slide'],'original_slide':original,
                      'title':titles[row['slide']],
                      'notes_en':english,'notes_vi':vietnamese,
                      'notes':'English\n\n'+english+'\n\nTiếng Việt\n\n'+vietnamese})
    (ROOT/'research/speaker-notes.json').write_text(json.dumps(notes,ensure_ascii=False,indent=2)+'\n')
    lines=[]
    for language,key in [('English','notes_en'),('Tiếng Việt','notes_vi')]:
        lines += [f'# {language}','']
        for row in notes:
            lines += [f"## Slide {row['slide']:02d}",'',row[key],'']
    (ROOT/'speaker-notes.md').write_text('\n'.join(lines))
    print(f"26 slides; English then Vietnamese; {sum(len(row['notes_en'].split()) for row in notes)} English words")
    return notes


if __name__=='__main__':
    write_notes()
