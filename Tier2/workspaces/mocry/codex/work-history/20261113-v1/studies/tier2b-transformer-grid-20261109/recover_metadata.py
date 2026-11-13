"""Recover completed fits after a version-string metadata serialization failure."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
import torch
from torch.torch_version import TorchVersion
import data as dataset
from model import Predictor,TARGETS
from fit_core import configure,dump,sha,tensors,normalised_prediction,score,eval_batch_for

ROOT=Path(__file__).resolve().parent


def tensor_hash(state):
    digest=hashlib.sha256()
    for key,value in sorted(state.items()):
        digest.update(key.encode());digest.update(str(value.dtype).encode());digest.update(str(tuple(value.shape)).encode())
        digest.update(value.contiguous().cpu().numpy().tobytes())
    return digest.hexdigest()


def main():
    assert not (ROOT/"METADATA_RECOVERY.json").exists(),"One-time historical recovery already completed; do not rerun."
    configure("cuda");f,x,data,mean,scale=dataset.prepare(False)
    old=(ROOT/"fit_core_initial_metadata.txt").read_text(encoding="utf-8")
    new=(ROOT/"fit_core.py").read_text(encoding="utf-8")
    assert old.replace('"device":device,"torch":torch.__version__,','"device":device,"torch":str(torch.__version__),')==new
    signature={n:sha(ROOT/n) for n in ("model.py","fit_core.py","data.py","inputs/model_daily.csv")};signature["torch"]=str(torch.__version__)
    rows=[]
    for path in sorted((ROOT/"checkpoints").glob("*.pt")):
        tag=path.stem;log=ROOT/"step_logs"/(tag+".csv");h=pd.read_csv(log)
        with torch.serialization.safe_globals([TorchVersion]):cp=torch.load(path,weights_only=True)
        before=tensor_hash(cp["state_dict"])
        end=h.iloc[-1];at=h.loc[h.global_step.eq(cp["best_step"])].iloc[0]
        epochs=int(end.epoch);steps=int(end.global_step)
        assert steps==18*epochs and (epochs==120 or epochs-int(cp["best_epoch"])==15)
        assert len(h)==steps+1 and np.isfinite(h[[p+"_eval_loss" for p in ("train","validation","test")]].to_numpy()).all()
        cp["torch"]=str(cp["torch"]);torch.save(cp,path)
        safe=torch.load(path,weights_only=True);assert tensor_hash(safe["state_dict"])==before
        target=cp["target"];family=cp["family"];j=TARGETS.index(target);length=int(cp["lookback"]);device=cp["device"]
        model=Predictor(family,j).to(device);model.load_state_dict(cp["state_dict"])
        d=tensors(x,data,j,length,device);exported={};metrics=[];max_difference=0.
        row={"run":tag,"target":target,"family":family,"lookback":length,"lr":float(cp["lr"]),"seed":int(cp["seed"]),
            "stage":"screen" if family=="Transformer" else "baseline_confirmation","device":device,"eval_batch":eval_batch_for(family,length),"parameters":int(cp["parameters"]),
            "best_epoch":int(cp["best_epoch"]),"best_step":int(cp["best_step"]),"epochs":epochs,"steps":steps,
            "best_train_loss":float(at.train_eval_loss),"best_validation_loss":float(at.validation_eval_loss),"test_loss_at_val_checkpoint":float(at.test_eval_loss),
            "last_train_loss":float(end.train_eval_loss),"last_validation_loss":float(end.validation_eval_loss),"last_test_loss":float(end.test_eval_loss),
            "seconds":float(end.elapsed_seconds),"checkpoint":path.relative_to(ROOT).as_posix(),"step_log":log.relative_to(ROOT).as_posix(),"metadata_recovered":True}
        for part,(xx,yy) in d.items():
            p=normalised_prediction(model,xx,row["eval_batch"]).cpu().numpy().ravel().astype(float)*scale[j]+mean[j]
            exported[part]=p;s=score(p,data[part]["truth"][:,j],scale[j]);max_difference=max(max_difference,abs(s["loss"]-at[part+"_eval_loss"]))
            metrics.append({"target":target,"family":family,"lookback":length,"lr":row["lr"],"seed":row["seed"],"stage":row["stage"],"split":part,**s})
        assert max_difference<1e-6
        np.savez_compressed(ROOT/"predictions"/(tag+".npz"),**exported)
        value={"row":row,"metrics":metrics,"signature":signature,"original_training_fit_core_sha256":sha(ROOT/"fit_core_initial_metadata.txt"),"numeric_state_sha256":before}
        dump(ROOT/"case_results"/(tag+".json"),value)
        rows.append({"run":tag,"state_sha256_before_after":before,"all_numeric_weights_unchanged":True,"max_normalised_loss_vs_log":max_difference,"completed_epochs":epochs})
        print("RECOVERED",tag,flush=True)
        del model,d
    dump(ROOT/"METADATA_RECOVERY.json",{"only_code_change":"Convert torch version metadata to ordinary str before saving; numeric training code unchanged",
        "original_fit_source_sha256":sha(ROOT/"fit_core_initial_metadata.txt"),"fixed_fit_source_sha256":sha(ROOT/"fit_core.py"),"fits":rows,"all_passed":True})


if __name__=="__main__":main()
