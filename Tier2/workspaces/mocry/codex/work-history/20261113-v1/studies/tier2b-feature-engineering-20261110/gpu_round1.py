"""Sequential on one GPU; a separate GPU process may finish the demand branch."""
import argparse
import torch
from fit import fit
from features import TARGETS,ROOT

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--targets',default='generation_MW,price_GBP_MWh');p.add_argument('--groups',default='weekly_context;regime;balance;price_robust;fuel_mix;weather_wind');args=p.parse_args()
    torch.set_num_threads(2);torch.set_num_interop_threads(1);torch.use_deterministic_algorithms(True);torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False;torch.cuda.set_per_process_memory_fraction(.8)
    for target in args.targets.split(','):
        for g in args.groups.split(';'):
            if (ROOT/'STOP_REQUESTED').exists():break
            for family in ['RNN','LSTM','Transformer']:
                for budget in [2000,5000,10000]:fit(target,family,budget,g.split('+'),17,'cuda')
