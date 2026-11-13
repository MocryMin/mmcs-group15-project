"""Same independent scalar forecasting architecture as the previous experiment."""
import numpy as np
import torch
from torch import nn


TARGETS=["generation_MW","demand_MW","price_GBP_MWh"]


class Predictor(nn.Module):
    def __init__(self,family,target_index):
        super().__init__();self.target_index=target_index
        hidden=68 if family=="RNN" else 32
        self.core=nn.RNN(8,hidden,batch_first=True,nonlinearity="tanh") if family=="RNN" else nn.LSTM(8,hidden,batch_first=True)
        self.dropout=nn.Dropout(.1);self.head=nn.Linear(hidden,1)
        nn.init.zeros_(self.head.weight);nn.init.zeros_(self.head.bias)

    def forward(self,x):
        hidden,_=self.core(x)
        return x[:,-1,self.target_index:self.target_index+1]+self.head(self.dropout(hidden[:,-1]))


def windows(x,origins,length):
    return np.stack([x[t-length+1:t+1] for t in origins]).astype(np.float32)
