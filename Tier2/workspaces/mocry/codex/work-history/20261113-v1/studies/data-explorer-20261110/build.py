"""Build one self-contained offline chart app from the frozen experiment CSV."""
from pathlib import Path
import csv
import hashlib
import json
import math
import sys

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/".deps"))
from plotly.offline import get_plotlyjs
import plotly

SOURCE=ROOT.parent/"tier2b-transformer-10x-20261110/inputs/model_daily.csv"
EXPECTED="addc31ee1e01de947c025eb2b47aa7a09e3680e3ca189ea904edf9bd73fae475"


def main():
    digest=hashlib.sha256(SOURCE.read_bytes()).hexdigest();assert digest==EXPECTED
    with SOURCE.open(encoding="utf-8-sig",newline="") as f:records=list(csv.DictReader(f))
    rows=[]
    for r in records:
        row=[r["date"],*[float(r[k]) for k in ("generation_MW","demand_MW","price_GBP_MWh","source_total_MW","wind_farm_MW")],r["strict_no_imputation"].lower() in ("1","true")]
        assert all(math.isfinite(v) for v in row[1:6]);assert abs(row[1]-row[4]-row[5])<1e-8
        rows.append(row)
    assert len({r[0] for r in rows})==len(rows) and rows==sorted(rows,key=lambda r:r[0])
    default=[r for r in rows if "2025-09-01"<=r[0]<="2026-08-31"];assert len(default)==365
    metadata={"source_csv":str(SOURCE),"source_sha256":digest,"rows":len(rows),"start":rows[0][0],"end":rows[-1][0],
        "default_start":"2025-09-01","default_end":"2026-08-31","default_samples":365,"plotly_python":plotly.__version__,
        "column_order":["date","generation_MW","demand_MW","price_GBP_MWh","source_total_MW","wind_farm_MW","strict_no_imputation"],
        "display_units":{"generation":"GW","demand":"GW","gap":"GW","price":"GBP/MWh"},"generation_includes_independent_windfarm":True,
        "offline":True,"network_dependencies":[],"quality_flag":"date-level strict_no_imputation false means estimation/interpolation used somewhere that day"}
    template=(ROOT/"explorer_template.html").read_text(encoding="utf-8")
    assert template.count("__DATA__")==1 and template.count("__PLOTLY_BUNDLE__")==1
    output=template.replace("__PLOTLY_BUNDLE__",get_plotlyjs()).replace("__DATA__",json.dumps({"metadata":metadata,"rows":rows},ensure_ascii=False,separators=(",",":"),allow_nan=False))
    (ROOT/"MMCS-data-explorer.html").write_text(output,encoding="utf-8")
    (ROOT/"SOURCE.json").write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"path":str(ROOT/"MMCS-data-explorer.html"),"bytes":len(output.encode()),**metadata},ensure_ascii=False))


if __name__=="__main__":main()
