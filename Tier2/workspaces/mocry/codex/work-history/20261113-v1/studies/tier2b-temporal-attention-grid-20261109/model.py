"""Unidirectional recurrent encoder with last-query temporal attention."""
import math
import numpy as np
import torch
from torch import nn

TARGETS=["generation_MW","demand_MW","price_GBP_MWh"]


class Predictor(nn.Module):
    def __init__(self,family,target_index):
        super().__init__()
        self.target_index=target_index
        hidden=68 if family=="RNN" else 32
        self.core=nn.RNN(8,hidden,batch_first=True,nonlinearity="tanh") if family=="RNN" else nn.LSTM(8,hidden,batch_first=True)
        self.dropout=nn.Dropout(.1)
        self.head=nn.Linear(2*hidden,1)
        nn.init.zeros_(self.head.weight)
        nn.init.zeros_(self.head.bias)

    @staticmethod
    def temporal_weights(states,mode="attention"):
        if mode=="attention":
            query=states[:,-1:,:]
            scores=torch.bmm(states,query.transpose(1,2)).squeeze(-1)/math.sqrt(states.shape[-1])
            return torch.softmax(scores,dim=1)
        if mode=="uniform":return torch.full_like(states[:,:,0],1./states.shape[1])
        if mode=="last_only":
            weights=torch.zeros_like(states[:,:,0]);weights[:,-1]=1.
            return weights
        raise ValueError(mode)

    def forward(self,x,return_attention=False,mode="attention"):
        states,_=self.core(x)
        weights=self.temporal_weights(states,mode)
        context=torch.bmm(weights.unsqueeze(1),states).squeeze(1)
        features=torch.cat([states[:,-1,:],context],dim=-1)
        prediction=x[:,-1,self.target_index:self.target_index+1]+self.head(self.dropout(features))
        return (prediction,weights) if return_attention else prediction


def windows(x,origins,length):
    return np.stack([x[t-length+1:t+1] for t in origins]).astype(np.float32)
