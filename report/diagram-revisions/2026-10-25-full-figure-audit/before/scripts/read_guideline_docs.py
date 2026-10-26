#!/usr/bin/env python3
"""Extract text from local Word 97-2003 templates (not their visual layout).

Read the CFB FAT/mini-FAT and Word CLX piece table; preserve Unicode Vietnamese.
Outputs text and hashes for a reproducible content audit, without editing templates.
"""
import struct, pathlib, hashlib, json, subprocess
u16=lambda b,o: struct.unpack_from('<H',b,o)[0]
u32=lambda b,o: struct.unpack_from('<I',b,o)[0]
def read_doc(path):
 b=path.read_bytes(); size=1<<u16(b,30); mini=1<<u16(b,32)
 sector=lambda n:b[(n+1)*size:(n+2)*size]
 dif=list(struct.unpack_from('<109I',b,76)); n=u32(b,68)
 for _ in range(u32(b,72)):
  d=struct.unpack('<'+str(size//4)+'I',sector(n)); dif.extend(d[:-1]); n=d[-1]
 fat=[]
 for n in dif[:u32(b,44)]: fat.extend(struct.unpack('<'+str(size//4)+'I',sector(n)))
 def chain(n,table,get):
  out=b''; seen=set()
  while n<0xfffffffa and n not in seen:
   seen.add(n); out+=get(n); n=table[n]
  return out
 directory=chain(u32(b,48),fat,sector); entries={}
 for o in range(0,len(directory),128):
  d=directory[o:o+128]; length=u16(d,64)
  if length: entries[d[:length-2].decode('utf-16le')]=(d[66],u32(d,116),struct.unpack_from('<Q',d,120)[0])
 root=next(v for v in entries.values() if v[0]==5); mini_data=chain(root[1],fat,sector)
 mf=chain(u32(b,60),fat,sector) if u32(b,64) else b''; minifat=list(struct.unpack('<'+str(len(mf)//4)+'I',mf))
 def stream(name):
  _,n,s=entries[name]
  return (chain(n,minifat,lambda i:mini_data[i*mini:(i+1)*mini]) if s<u32(b,56) else chain(n,fat,sector))[:s]
 w=stream('WordDocument'); t=stream('1Table' if u16(w,10)&512 else '0Table')
 o=32; o+=2+u16(w,o)*2; o+=2+u16(w,o)*4; o+=2
 fc,lcb=struct.unpack_from('<II',w,o+33*8); clx=t[fc:fc+lcb]; pos=0
 while clx[pos]==1: pos+=3+u16(clx,pos+1)
 assert clx[pos]==2
 plc=clx[pos+5:pos+5+u32(clx,pos+1)]; n=(len(plc)-4)//12; cps=struct.unpack_from('<'+str(n+1)+'I',plc); text=''
 for i in range(n):
  off=u32(plc,4*(n+1)+8*i+2); compressed=bool(off&0x40000000); off&=0x3fffffff
  if compressed: off//=2
  count=cps[i+1]-cps[i]
  text+=w[off:off+count*(1 if compressed else 2)].decode('cp1252' if compressed else 'utf-16le',errors='replace')
 return text.replace('\r','\n').replace('\x07',' | ').replace('\x0b','\n')
def main():
 root = pathlib.Path(__file__).resolve().parents[1]
 out = root / 'generated/guideline-text'; out.mkdir(parents=True, exist_ok=True)
 hashes = {}
 templates = sorted((root / 'guideline/template').glob('*.doc')) + sorted((root / 'guideline/template').glob('*.pdf'))
 if not templates:
  raise FileNotFoundError('No templates found in report/guideline/template')
 for p in templates:
  text = (read_doc(p) if p.suffix == '.doc' else subprocess.check_output(['pdftotext', '-layout', str(p), '-'], text=True))
  # Strip Word field control markers; preserve tabs, newlines and form feeds.
  text = ''.join(c for c in text if ord(c) >= 32 or c in '\n\t\f')
  text = '\n'.join(line.rstrip() for line in text.splitlines()).rstrip() + '\n'
  target = out / (p.stem + ('.pdf.txt' if p.suffix == '.pdf' else '.txt')); target.write_text(text)
  hashes[str(p.relative_to(root))] = {'text_path': str(target.relative_to(root)), 'source_sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
                                    'text_sha256': hashlib.sha256(target.read_bytes()).hexdigest()}
 (out / 'provenance.json').write_text(json.dumps(hashes, ensure_ascii=False, indent=2) + '\n')
 print(f'Extracted {len(hashes)} Word/PDF templates; text only, not layout conversion.')

if __name__ == '__main__':
 main()
