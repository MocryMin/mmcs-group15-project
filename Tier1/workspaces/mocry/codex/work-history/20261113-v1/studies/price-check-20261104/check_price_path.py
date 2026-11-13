"""Read-only audit of the price data actually saved in Baseline 1104."""
from pathlib import Path
import calendar
import csv
from datetime import datetime
import gzip
import hashlib
import json
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parent
REPO=PROJECT/"group-collaboration"
PACKAGE=REPO/"Tier1/workspaces/mocry/codex/baseline-1104/20261104-v1"
CALC=PACKAGE/"calculation"
release=REPO/"Tier1/public/data_quality/full_data_repair/20261104-v2"
new=pd.read_csv(release/"data/daily_market_index_price.csv",index_col=0,parse_dates=True).iloc[:,0]
old=pd.read_csv(REPO/"daily_market_index_price.csv",index_col=0,parse_dates=True).iloc[:,0]
legacy=pd.read_csv(REPO/"Tier1/public/research_1103/controller/mocry-codex/20261103-v1.1/R4-finance-data/prices_gbp2020.csv",index_col=0,parse_dates=True)
inputs=pd.read_csv(CALC/"model_inputs.csv",index_col=0,parse_dates=True)
cpi={}
with (PACKAGE/"inputs/finance/ONS-CPI-CSV.csv").open(encoding="utf-8-sig",newline="") as stream:
    for row in csv.reader(stream):
        try: cpi[datetime.strptime(row[0],"%Y %b").strftime("%Y-%m")]=float(row[1])
        except (ValueError,IndexError): pass
def actual_real(series):
    return pd.Series([float(v)*108.7/cpi[t.strftime("%Y-%m")] for t,v in series.items()],index=series.index)
real=actual_real(new)
oldreal=actual_real(old)
input_error=float(np.max(np.abs(inputs.price-real.loc[inputs.index])))
assert input_error<1e-8
results=json.loads((CALC/"results.json").read_text(encoding="utf-8"))
checks=[]
for r in results:
    f=pd.read_csv(CALC/"outputs"/(r["case"]+".csv"),index_col=0,parse_dates=True)
    deliberately_old="_old_price_matched" in r["case"]
    expected=(oldreal if deliberately_old else real).loc[f.index]
    error=float(np.max(np.abs(f.price-expected)))
    years=sum(1/(366 if calendar.isleap(t.year) else 365) for t in f.index)
    revenue=float(np.dot(expected,f.q+f.d))*1000/years
    cash_error=abs(revenue-r["electricity_revenue_GBP2020_year"])
    assert error<1e-8 and cash_error<.01,(r["case"],error,cash_error)
    checks.append(dict(case=r["case"],source="old-price comparison" if deliberately_old else "corrected v2",max_price_error=error,revenue_error_GBP2020=cash_error))
raw=json.loads(gzip.decompress((release/"evidence/mid.json.gz").read_bytes()))["days"]
examples=[]
for date in ["2020-01-01","2023-05-09"]:
    periods=raw[date]; flat=[]; active=[]; zero=0; providers=set()
    for stamp,records in periods.items():
        providers.update(records)
        flat.extend(v[0] for v in records.values())
        zero+=sum(v[1]<=0 for v in records.values())
        traded=[v for v in records.values() if v[1]>0]
        active.append(sum(price*volume for price,volume in traded)/sum(volume for _,volume in traded))
    fixed=sum(active)/len(active); diluted=sum(flat)/len(flat)
    assert abs(fixed-new.loc[pd.Timestamp(date)])<1e-8
    examples.append(dict(date=date,periods=len(periods),provider_records=len(flat),zero_volume_records=zero,providers=sorted(providers),flat_price=diluted,active_daily_price=fixed,ratio=fixed/diluted,course_value=float(old.loc[pd.Timestamp(date)])))
by={r["case"]:r for r in results}
report=dict(
    verdict="Baseline1104 main calculations use corrected prices; only two explicitly labelled old-price comparisons use course prices.",
    model_input_dates=len(inputs),max_model_input_price_error=input_error,
    cases_checked=len(checks),corrected_price_cases=sum(x["source"]=="corrected v2" for x in checks),
    old_price_comparisons=[x["case"] for x in checks if x["source"]!="corrected v2"],
    max_case_price_error=max(x["max_price_error"] for x in checks),max_electricity_revenue_error_GBP2020=max(x["revenue_error_GBP2020"] for x in checks),
    examples=examples,
    design2023_mean_real_price=dict(corrected=float(real.loc["2023"].mean()),legacy=float(legacy.loc["2023","real_2020_GBP_per_MWh"].mean())),
    policy_A_design2023_increment_GBP2020_year=dict(old_comparison=by["A_old_price_matched"]["increment_GBP2020_year"],corrected_main=by["A_both_design2023"]["increment_GBP2020_year"]),
    old_research_file_status="derived from unrepaired course prices; superseded for model-input use",
    CU_message="ceb9095432fb43048540c0688b466c8c",remote_sync_head="9f5efb3b56f3843349bb8fd37f4d2febd9844d68",
    recalculation_required_for_price_bug=False,checks=checks)
(HERE/"PRICE_CHECK.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({k:v for k,v in report.items() if k!="checks"},ensure_ascii=False,indent=2))
