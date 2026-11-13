from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parent/'strict-confirmation'
sys.path.insert(0,str(ROOT))
import torch
from fit import fit
torch.set_num_threads(2);torch.set_num_interop_threads(1);torch.use_deterministic_algorithms(True);torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False;torch.cuda.set_per_process_memory_fraction(.8)
plan=json.loads((ROOT/'PLAN_FROZEN.json').read_text())['plan']
for r in plan:
    for seed in [17,29,43]:fit(r['target'],r['family'],int(r['budget']),r['groups'].split('+'),seed,'cuda')
