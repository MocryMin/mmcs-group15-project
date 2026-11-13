"""Freeze the audited fixed-policy study before testing plateau interventions."""
from pathlib import Path
import hashlib
import json
import zipfile

ROOT=Path(__file__).resolve().parent
OLD=ROOT.parent/"MMCS_Tier2B_Joint_RNN_LSTM_10x_20261110_v1.1.zip"
EXPECTED="011ad3bcd8f6c30222a5c39f3e79729cdf19c6f915897f361c5ff99777e731c7"


def write_once(p,content):
    p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():assert p.read_bytes()==content,p
    else:p.write_bytes(content)


def main():
    assert hashlib.sha256(OLD.read_bytes()).hexdigest()==EXPECTED
    with zipfile.ZipFile(OLD) as z:
        manifest=json.loads(z.read("MANIFEST.json"))
        for n,v in manifest.items():assert hashlib.sha256(z.read(n)).hexdigest()==v["sha256"]
        for n in ("model.py","data.py","inputs/model_daily.csv","inputs/SOURCE_MANIFEST.json","requirements.txt","CONFIGS_FROZEN.json"):
            write_once(ROOT/n,z.read(n))
        for n in ("model.py","data.py","fit_core.py","scalers.json","splits.csv","PROTOCOL.json","results/ALL_METRICS.csv","results/training_runs.csv","results/SUMMARY.csv","results/AUDIT.json","results/SIMPLE_BASELINES.csv"):
            write_once(ROOT/"reference"/n,z.read(n))
    write_once(ROOT/"reference"/OLD.name,OLD.read_bytes())
    record={"archive":OLD.name,"sha256":EXPECTED,"files_verified":len(manifest),"purpose":"Immutable prior15-epoch-patience fixed-policy study; all new arms use matched30-epoch patience","data_model_features_windows_unchanged":True}
    write_once(ROOT/"REFERENCE.json",(json.dumps(record,indent=2)+"\n").encode())
    print(json.dumps(record))


if __name__=="__main__":main()
