"""Check the new attention calculation, gradients, parameter count and baseline alignment."""
from pathlib import Path
import importlib.util
import math
import json
import numpy as np
import torch
from model import Predictor
from fit_core import dump
import data as dataset

ROOT=Path(__file__).resolve().parent


def main():
    torch.set_num_threads(2)
    f,x,d,mean,scale=dataset.prepare()
    baseline=json.loads((ROOT/"baseline/scalers.json").read_text())
    checks={"same_training_scalers_as_baseline":np.array_equal(mean,baseline["mean"]) and np.array_equal(scale,baseline["std"])}
    spec=importlib.util.spec_from_file_location("baseline_model",ROOT/"baseline/model.py")
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    # Tiny independent NumPy calculation checks score direction and normalisation.
    states=np.array([[[.1,.2],[.3,-.1],[-.2,.4]]],dtype=np.float32)
    logits=np.sum(states*states[:,-1:,:],axis=-1)/math.sqrt(2)
    expected=np.exp(logits-logits.max(axis=1,keepdims=True));expected/=expected.sum(axis=1,keepdims=True)
    actual=Predictor.temporal_weights(torch.from_numpy(states)).numpy()
    checks["attention_matches_independent_numpy"]=np.allclose(actual,expected,atol=1e-7)
    for family in ("RNN","LSTM"):
        torch.manual_seed(17);model=Predictor(family,0)
        torch.manual_seed(17);plain=module.Predictor(family,0)
        checks[family+"_same_initial_backbone"]=all(torch.equal(p,q) for p,q in zip(model.core.parameters(),plain.core.parameters()))
        checks[family+"_5441_parameters"]=sum(p.numel() for p in model.parameters())==5441
        batch=torch.from_numpy(np.stack([x[t-364:t+1] for t in d["train"]["origins"][:4]]))
        model.eval();prediction,weights=model(batch,return_attention=True)
        checks[family+"_uses_all_365_positions"]=weights.shape==(4,365)
        checks[family+"_normalised_nonnegative_weights"]=bool(torch.all(weights>=0) and torch.allclose(weights.sum(dim=1),torch.ones(4),atol=1e-6))
        checks[family+"_initial_persistence"]=torch.equal(prediction,batch[:,-1,0:1])
        # Give the context head a nonzero coefficient to test differentiability at older positions.
        with torch.no_grad():model.head.weight[:,model.head.in_features//2:]=.01
        batch.requires_grad_(True);model.zero_grad(set_to_none=True);model(batch).sum().backward()
        checks[family+"_finite_backprop_to_early_history"]=bool(torch.isfinite(batch.grad).all() and batch.grad[:,:100,:3].abs().sum()>0)
    checks={k:bool(v) for k,v in checks.items()}
    result={"checks":checks,"all_passed":all(checks.values()),"source":"Frozen preceding plain RNN/LSTM grid; no new data","attention":"Last hidden state as query; all observed hidden states as keys and values; no Q/K/V projection matrices"}
    dump(ROOT/"PREFLIGHT.json",result);assert result["all_passed"],result
    print(json.dumps(result))


if __name__=="__main__":main()
