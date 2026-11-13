"""Extract local manufacturer documents without changing their originals."""
import hashlib
import json
from pathlib import Path
import pymupdf

ROOT=Path(__file__).resolve().parents[1]
for path in sorted((ROOT/'evidence').glob('*.pdf')):
    reader=pymupdf.open(path)
    pages=[dict(page=i+1,text=p.get_text(sort=True) or '') for i,p in enumerate(reader)]
    output=dict(file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),pages=pages)
    path.with_suffix('.pages.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    path.with_suffix('.txt').write_text('\n\n'.join('PAGE '+str(p['page'])+'\n'+p['text'] for p in pages),encoding='utf-8')
    print(path.name,'PAGES',len(pages),'CHARS',sum(len(p['text']) for p in pages),flush=True)
