"""Portable build from the versioned application data, using only Python stdlib."""
from pathlib import Path
import csv,json
R=Path(__file__).resolve().parent
data=json.loads((R/'data/app-data.json').read_text(encoding='utf-8'))
rows=data['rows'];meta=data['metadata'];cols=meta['column_order']
assert len(rows)==meta['rows'] and len({r[0] for r in rows})==len(rows)
assert all(len(r)==len(cols) for r in rows)
assert rows==sorted(rows,key=lambda r:r[0])
assert (R/'dist/assets/echarts.min.js').exists(),'Restore the tracked ECharts bundle before building.'
template=(R/'src/index.html').read_text(encoding='utf-8');assert template.count('__DATA__')==1
(R/'dist/index.html').write_text(template.replace('__DATA__',json.dumps(data,ensure_ascii=False,separators=(',',':'),allow_nan=False)).replace('__APP_JS__',(R/'src/app.js').read_text(encoding='utf-8')),encoding='utf-8')
(R/'dist/data').mkdir(exist_ok=True)
with (R/'dist/data/daily.csv').open('w',encoding='utf-8-sig',newline='') as stream:
    w=csv.writer(stream);w.writerow(cols);w.writerows(rows)
(R/'dist/data/metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(R/'dist/data/forecast-gaps.json').write_bytes((R/'data/forecast-gaps.json').read_bytes())
print(json.dumps({'built':True,'version':meta['version'],'rows':len(rows)}))

legacy=R.parents[1]/'assignments/FinalProject/data-explorer-20261110'
if legacy.exists():
 old=legacy/'MMCS-data-explorer.html';backup=legacy/'MMCS-data-explorer-v2.0.0.html'
 if old.exists() and not backup.exists():backup.write_bytes(old.read_bytes())
 html=(R/'dist/index.html').read_text(encoding='utf-8').replace('<script src="assets/echarts.min.js"></script>','<script>'+(R/'dist/assets/echarts.min.js').read_text(encoding='utf-8')+'</script>')
 old.write_text(html,encoding='utf-8')
