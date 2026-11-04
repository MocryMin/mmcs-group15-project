"""Re-run the packaged study into a fresh directory and compare saved results."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import json
import os
import runpy
import sys

ROOT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument("--output",type=Path)
args=parser.parse_args()
out=args.output.resolve() if args.output else ROOT/"reproduced"/datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
if out.exists() and any(out.iterdir()):
    raise SystemExit("Choose an empty output directory; archived results will not be overwritten.")
if out==ROOT or out.is_relative_to(ROOT/"calculation") or out.is_relative_to(ROOT/"inputs"):
    raise SystemExit("Choose a separate output directory.")
out.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT/"calculation"))
import run_baseline as rb
rb.HERE=out
sys.argv=[str(ROOT/"calculation/run_baseline.py")]
rb.main()
import verify_baseline as vb
vb.HERE=out
vb.main()
os.environ["MMCS_BASELINE_OUTPUT"]=str(out)
runpy.run_path(str(ROOT/"calculation/build_summary.py"),run_name="__main__")
original={r["case"]:r for r in json.loads((ROOT/"calculation/results.json").read_text(encoding="utf-8"))}
rerun={r["case"]:r for r in json.loads((out/"results.json").read_text(encoding="utf-8"))}
assert original.keys()==rerun.keys()
largest=0.
for name,ref in original.items():
    got=rerun[name]
    assert ref["battery_units"]==got["battery_units"] and ref["electrolyser_units"]==got["electrolyser_units"],name
    for key in ["net_profit_GBP2020_year","increment_GBP2020_year"]:
        error=abs(ref[key]-got[key]); largest=max(largest,error)
        assert error<1.,(name,key,error)
receipt={"cases":len(original),"same_installed_counts":True,"max_profit_difference_GBP2020":largest,"all_checks_passed":True}
(out/"REPRODUCTION_CHECK.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
print(json.dumps(receipt,indent=2))
print("Reproduced outputs:",out)
