"""One shared recurrent encoder predicts the three next-day targets together."""
import numpy as np
import torch
from torch import nn

TARGETS=["generation_MW","demand_MW","price_GBP_MWh"]
WIDTHS={"RNN":{"small":68,"large":228},"LSTM":{"small":32,"large":112}}
COUNTS={"RNN":{"small":5511,"large":54951},"LSTM":{"small":5475,"large":54995}}


class Predictor(nn.Module):
    def __init__(self,family,budget):
        super().__init__();self.family=family;self.budget=budget
        h=WIDTHS[family][budget]
        self.core=nn.RNN(8,h,batch_first=True,nonlinearity="tanh") if family=="RNN" else nn.LSTM(8,h,batch_first=True)
        self.dropout=nn.Dropout(.1);self.head=nn.Linear(h,3)
        nn.init.zeros_(self.head.weight);nn.init.zeros_(self.head.bias)

    def forward(self,x):
        hidden,_=self.core(x)
        return x[:,-1,:3]+self.head(self.dropout(hidden[:,-1]))


def windows(x,origins,length):
    return np.stack([x[t-length+1:t+1] for t in origins]).astype(np.float32)
