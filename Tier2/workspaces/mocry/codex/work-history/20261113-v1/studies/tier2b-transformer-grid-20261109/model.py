"""Parameter-matched one-layer Transformer and frozen recurrent reference architectures."""
import math
import numpy as np
import torch
from torch import nn
from torch.nn.attention import sdpa_kernel,SDPBackend

TARGETS=["generation_MW","demand_MW","price_GBP_MWh"]


class Predictor(nn.Module):
    def __init__(self,family,target_index):
        super().__init__();self.family=family;self.target_index=target_index
        self.dropout=nn.Dropout(.1)
        if family=="Transformer":
            self.input_projection=nn.Linear(8,24)
            self.encoder=nn.TransformerEncoderLayer(d_model=24,nhead=3,dim_feedforward=54,
                dropout=.1,activation="gelu",batch_first=True,norm_first=True)
            self.head=nn.Linear(24,1)
            lag=torch.arange(365,dtype=torch.float32).unsqueeze(1)
            frequency=torch.exp(torch.arange(0,24,2,dtype=torch.float32)*(-math.log(10000.)/24))
            pe=torch.zeros(365,24);pe[:,0::2]=torch.sin(lag*frequency);pe[:,1::2]=torch.cos(lag*frequency)
            self.register_buffer("position",pe,persistent=False)
        else:
            hidden=68 if family=="RNN" else 32
            self.core=nn.RNN(8,hidden,batch_first=True,nonlinearity="tanh") if family=="RNN" else nn.LSTM(8,hidden,batch_first=True)
            self.head=nn.Linear(hidden,1)
        nn.init.zeros_(self.head.weight);nn.init.zeros_(self.head.bias)

    def forward(self,x):
        if self.family=="Transformer":
            # All tokens are observed history; the forecast target is outside this window.
            # Latest observed day has relative position zero for every lookback length.
            tokens=self.input_projection(x)+self.position[:x.shape[1]].flip(0).unsqueeze(0)
            with sdpa_kernel(SDPBackend.MATH):hidden=self.encoder(tokens)
        else:hidden,_=self.core(x)
        return x[:,-1,self.target_index:self.target_index+1]+self.head(self.dropout(hidden[:,-1]))


def windows(x,origins,length):
    return np.stack([x[t-length+1:t+1] for t in origins]).astype(np.float32)
