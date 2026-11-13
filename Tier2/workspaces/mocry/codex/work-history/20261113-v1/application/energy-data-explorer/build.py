"""Build the maintained static app and refresh the original offline GUI."""
from pathlib import Path
from datetime import datetime,timezone
import base64,csv,gzip,hashlib,importlib.util,json,statistics,sys

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[1]/'assignments/FinalProject'
LEGACY=PROJECT/'data-explorer-20261110'
FROZEN=PROJECT/'tier2b-feature-engineering-20261110'
sys.path.insert(0,str(LEGACY/'.deps'))


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    for folder in ['dist/assets','dist/data','data','evidence','releases']:(ROOT/folder).mkdir(parents=True,exist_ok=True)
    rawpath=ROOT/'evidence/forecast_snapshots.json.gz'
    encoded=rawpath.with_suffix(rawpath.suffix+'.b64')
    if encoded.exists():rawpath.write_bytes(base64.b64decode(encoded.read_text()))
    forecasts=json.loads(gzip.decompress(rawpath.read_bytes()))
    fc={r['date']:r for r in forecasts['records']};assert len(fc)==2086
    p=PROJECT/'data-repair-20261104-v2/repair_data.py'
    spec=importlib.util.spec_from_file_location('repair_reference',p);repair=importlib.util.module_from_spec(spec);spec.loader.exec_module(repair)
    bundlepath=PROJECT/'data-repair-20261104-v2/evidence/neso.json.gz'
    with gzip.open(bundlepath,'rt',encoding='utf-8') as stream:bundle=json.load(stream)
    actual=repair.parse_neso(bundle)
    with (FROZEN/'inputs/model_daily.csv').open(encoding='utf-8-sig',newline='') as stream:base=list(csv.DictReader(stream))
    with (FROZEN/'features/neso_demand.csv').open(encoding='utf-8-sig',newline='') as stream:
        from datetime import date,timedelta
        cardinal={(date.fromisoformat(r['date'])+timedelta(days=1)).isoformat():r for r in csv.DictReader(stream)}
    rows=[];issues=[]
    for b in base:
        d=b['date'];a=actual[d];assert len(a)==48
        r=fc[d];points=r.get('slots',[]);cutoff=d+'T00:00:00Z'
        assert len({x['startTime'] for x in points})==len(points)
        for x in points:assert x['boundary']=='N' and x['startTime'][:10]==d and x['publishTime']<cutoff
        for key,field in [('nd_forecast_MW','nationalDemand'),('tsd_forecast_MW','transmissionSystemDemand')]:
            if r.get(key) is not None:
                accepted=[x[field] for x in points if isinstance(x.get(field),(int,float)) and x[field]>0]
                assert len(accepted)==48 and abs(statistics.mean(accepted)-r[key])<1e-8
        old=cardinal.get(d)
        # The original feature pipeline carries forward one missing forecast;
        # a chart of original observations leaves that day visibly missing.
        c=float(old['neso_demand_mean']) if old and float(old['missing_forecast'])==0 else None
        row=[d,*[float(b[k]) for k in ['generation_MW','demand_MW','price_GBP_MWh','source_total_MW','wind_farm_MW']],b['strict_no_imputation'].lower() in ('true','1'),statistics.mean(v[1] for v in a.values()),statistics.mean(v[0] for v in a.values()),r.get('nd_forecast_MW'),r.get('tsd_forecast_MW'),c,r['nd_periods'],r['tsd_periods'],r.get('latest_issue')]
        rows.append(row)
        if row[9] is None or row[10] is None:issues.append({'date':d,'ND_periods':r['nd_periods'],'TSD_periods':r['tsd_periods'],'error':r.get('error')})
    assert len(rows)==2086 and rows==sorted(rows,key=lambda x:x[0])
    cols=['date','generation_MW','demand_MW','price_GBP_MWh','source_total_MW','wind_farm_MW','strict_no_imputation','NESO_ND_actual_MW','NESO_TSD_actual_MW','NESO_ND_forecast_MW','NESO_TSD_forecast_MW','NESO_ND_cardinal_mean_MW','ND_forecast_halfhours','TSD_forecast_halfhours','forecast_latest_issue_UTC']
    metadata={'version':'2.1.0','updated_at':datetime.now(timezone.utc).isoformat(),'rows':len(rows),'start':rows[0][0],'end':rows[-1][0],'default_start':'2025-09-01','default_end':'2026-08-31','column_order':cols,'daily_boundary':'UTC00:00-24:00;48half-hour slots','forecast_rule':forecasts['method'],'actual_source':'https://www.neso.energy/data-portal/historic-demand-data','forecast_source':'https://bmrs.elexon.co.uk/api-documentation/endpoint/forecast/demand/day-ahead/history','cardinal_source':'https://api.neso.energy/api/3/action/package_show?id=1-day-ahead-demand-forecast','coverage':{'ND_actual':sum(r[7] is not None for r in rows),'TSD_actual':sum(r[8] is not None for r in rows),'ND_forecast':sum(r[9] is not None for r in rows),'TSD_forecast':sum(r[10] is not None for r in rows),'ND_cardinal_mean':sum(r[11] is not None for r in rows)},'input_sha256':sha(FROZEN/'inputs/model_daily.csv'),'actual_bundle_sha256':sha(bundlepath),'forecast_snapshot_sha256':sha(rawpath),'forecast_retrieved_at':forecasts['retrieved_at'],'missing_forecasts':'No interpolation or forward fill;display gaps unless48 valid halfhours;detailsinCSV','forecast_distinction':'New NDF/TSDF curves are half-hourly as-of-day-start mean; old ND feature is cardinal-point arithmetic mean. Prior training runs unchanged.','offline':True,'network_dependencies':[]}
    data={'metadata':metadata,'rows':rows};payload=json.dumps(data,ensure_ascii=False,separators=(',',':'),allow_nan=False)
    (ROOT/'data/app-data.json').write_text(payload,encoding='utf-8')
    (ROOT/'data/forecast-gaps.json').write_text(json.dumps(issues,indent=2)+'\n',encoding='utf-8')
    template=(ROOT/'src/index.html').read_text(encoding='utf-8');assert template.count('__DATA__')==1
    app=template.replace('__DATA__',payload).replace('__APP_JS__',(ROOT/'src/app.js').read_text(encoding='utf-8'))
    (ROOT/'dist/index.html').write_text(app,encoding='utf-8')
    with (ROOT/'dist/data/daily.csv').open('w',encoding='utf-8-sig',newline='') as stream:w=csv.writer(stream);w.writerow(cols);w.writerows(rows)
    (ROOT/'dist/data/metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (ROOT/'dist/data/forecast-gaps.json').write_text(json.dumps(issues,indent=2)+'\n',encoding='utf-8')
    (ROOT/'DATA_AUDIT.json').write_text(json.dumps({'passed':True,'rows':len(rows),'coverage':metadata['coverage'],'missing_forecast_days':len(issues),'forecast_requests_failed':sum(bool(r.get('error')) for r in fc.values()),'all_forecast_issues_before_target_start':True,'exact_48_UTC_halfhours_required':True,'zero_imputation':True,'raw_snapshot_sha256':sha(rawpath),'existing_training_data_sha256':metadata['input_sha256']},indent=2)+'\n',encoding='utf-8')
    # Preserve the original GUI version once, then keep the known path current.
    old=LEGACY/'MMCS-data-explorer.html';backup=LEGACY/'MMCS-data-explorer-v1-original.html'
    if old.exists() and not backup.exists():backup.write_bytes(old.read_bytes())
    offline=app.replace('<script src="assets/echarts.min.js"></script>','<script>'+(ROOT/'dist/assets/echarts.min.js').read_text(encoding='utf-8')+'</script>')
    old.write_text(offline,encoding='utf-8')
    (LEGACY/'APP_LOCATION.json').write_text(json.dumps({'maintained_source':str(ROOT),'version':metadata['version'],'offline_refreshed':True},indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'built':True,'version':metadata['version'],'rows':len(rows),'coverage':metadata['coverage'],'forecast_gaps':len(issues)},ensure_ascii=False))

if __name__=='__main__':main()
