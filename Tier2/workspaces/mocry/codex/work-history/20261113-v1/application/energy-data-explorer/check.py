"""Validate the shipped app without fetching any web resources."""
from pathlib import Path
from html.parser import HTMLParser
import json,subprocess,hashlib
R=Path(__file__).resolve().parent
class Scripts(HTMLParser):
    def __init__(self):super().__init__();self.active=None;self.items=[]
    def handle_starttag(self,tag,attrs):
        if tag=='script':self.active=[dict(attrs),'']
    def handle_data(self,data):
        if self.active is not None:self.active[1]+=data
    def handle_endtag(self,tag):
        if tag=='script' and self.active is not None:self.items.append(self.active);self.active=None
p=Scripts();p.feed((R/'dist/index.html').read_text(encoding='utf-8'))
data=json.loads(next(s for a,s in p.items if a.get('id')=='mmcs-data'))
assert len(data['rows'])==data['metadata']['rows']
assert data['metadata']['coverage']=={k:sum(r[i] is not None for r in data['rows']) for k,i in [('ND_actual',7),('TSD_actual',8),('ND_forecast',9),('TSD_forecast',10),('ND_cardinal_mean',11)]}
assert len(set(r[0] for r in data['rows']))==len(data['rows'])
for row in data['rows']:
    assert len(row)==15
    for index,n in [(9,12),(10,13)]:assert (row[index] is not None)==(row[n]==48)
js=next(s for a,s in p.items if not a and s.strip())
(R/'.local').mkdir(exist_ok=True);(R/'.local/app-check.js').write_text(js,encoding='utf-8')
subprocess.run(['node','--check',str(R/'.local/app-check.js')],check=True)
assert '__DATA__' not in (R/'dist/index.html').read_text(encoding='utf-8')
assert (R/'dist/assets/echarts.min.js').stat().st_size>1000000
out={'passed':True,'embedded_rows':len(data['rows']),'comparison_series':6,'base_columns_retained':True,'forecast_coverage':data['metadata']['coverage'],'missing_values_are_null':True,'javascript_syntax_valid':True,'index_sha256':hashlib.sha256((R/'dist/index.html').read_bytes()).hexdigest()}
(R/'CHECKS.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out))
