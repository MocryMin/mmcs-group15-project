"""Freeze the audited small-model release and preserve its exact data/trainer."""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile

ROOT=Path(__file__).resolve().parent
OLD=ROOT.parent/"tier2b-transformer-grid-20261109"
ARCHIVE=ROOT.parent/"MMCS_Tier2B_Transformer_Grid_20261109.zip"
EXPECTED="ee0fbe39e22cf8f7847227930c83564f4181ac97f815b11aca7d1e47465e39a2"


def write_once(path,content):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():assert path.read_bytes()==content,path
    else:path.write_bytes(content)


def main():
    assert hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()==EXPECTED
    with zipfile.ZipFile(ARCHIVE) as z:
        manifest=json.loads(z.read("MANIFEST.json"))
        for name,record in manifest.items():
            assert hashlib.sha256(z.read(name)).hexdigest()==record["sha256"],name
        for name in ("data.py","inputs/model_daily.csv","inputs/SOURCE_MANIFEST.json","requirements.txt"):
            write_once(ROOT/name,z.read(name))
        model=z.read("model.py").decode("utf-8")
        enlarged=model.replace("24","72").replace("dim_feedforward=54","dim_feedforward=220")
        enlarged=enlarged.replace("Parameter-matched one-layer Transformer and frozen recurrent reference architectures.","Width-scaled one-layer Transformer; all other architecture choices retained.")
        write_once(ROOT/"model.py",enlarged.encode("utf-8"))
        trainer=z.read("fit_core.py").decode("utf-8")
        assert trainer.count('"Transformer":5407')==1
        write_once(ROOT/"fit_core.py",trainer.replace('"Transformer":5407','"Transformer":54005').encode("utf-8"))
        selection=json.loads(z.read("results/SELECTION_FROZEN.json"))
        write_once(ROOT/"CONFIGS_FROZEN.json",(json.dumps(selection,indent=2)+"\n").encode())
        for name in ("scalers.json","splits.csv","PROTOCOL.json","results/AUDIT.json","results/THREE_SEED_SUMMARY.csv","results/CONFIRMATION_METRICS.csv","results/training_runs.csv","results/TRANSFORMER_VS_RECURRENT.csv","results/SIMPLE_BASELINES.csv"):
            write_once(ROOT/"reference"/name,z.read(name))
    write_once(ROOT/"reference"/ARCHIVE.name,ARCHIVE.read_bytes())
    record={"archive":ARCHIVE.name,"sha256":EXPECTED,"verified_files":len(manifest),"base_parameters":5407,"expanded_parameters":54005,
        "scale_factor":54005/5407,"data_and_split_unchanged":True,"only_training_code_change":"COUNTS Transformer 5407 -> 54005; training arithmetic unchanged",
        "architecture_change":"d_model 24 -> 72, FFN 54 -> 220; depth1/heads3/dropout0.1/relative sinusoidal position/last-token residual readout unchanged"}
    write_once(ROOT/"REFERENCE.json",(json.dumps(record,indent=2)+"\n").encode())
    print(json.dumps(record))


if __name__=="__main__":main()
