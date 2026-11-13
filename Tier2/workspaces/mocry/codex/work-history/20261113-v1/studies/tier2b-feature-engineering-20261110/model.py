import math
import torch
from torch import nn
from torch.nn.attention import sdpa_kernel,SDPBackend

def specification(family,inputs,budget):
    if family=='RNN':
        h=min(range(4,200),key=lambda h:abs(h*h+(inputs+3)*h+1-budget));return {'hidden':h}
    if family=='LSTM':
        h=min(range(4,150),key=lambda h:abs(4*h*h+(4*inputs+9)*h+1-budget));return {'hidden':h}
    d={2000:16,5000:24,10000:32}[budget]
    ff=min(range(4,250),key=lambda ff:abs(4*d*d+(2*d+1)*ff+(inputs+11)*d+1-budget))
    return {'d_model':d,'heads':{16:2,24:3,32:4}[d],'ff':ff}

class Predictor(nn.Module):
    def __init__(self,family,j,inputs,budget):
        super().__init__();self.family=family;self.j=j;self.spec=specification(family,inputs,budget);self.dropout=nn.Dropout(.1)
        if family=='Transformer':
            d=self.spec['d_model'];self.projection=nn.Linear(inputs,d)
            self.encoder=nn.TransformerEncoderLayer(d,self.spec['heads'],self.spec['ff'],dropout=.1,activation='gelu',batch_first=True,norm_first=True)
            self.head=nn.Linear(d,1);lag=torch.arange(365,dtype=torch.float32).unsqueeze(1);freq=torch.exp(torch.arange(0,d,2,dtype=torch.float32)*(-math.log(10000.)/d));pe=torch.zeros(365,d);pe[:,0::2]=torch.sin(lag*freq);pe[:,1::2]=torch.cos(lag*freq);self.register_buffer('position',pe,persistent=False)
        else:
            h=self.spec['hidden'];self.core=nn.RNN(inputs,h,batch_first=True) if family=='RNN' else nn.LSTM(inputs,h,batch_first=True);self.head=nn.Linear(h,1)
        nn.init.zeros_(self.head.weight);nn.init.zeros_(self.head.bias)
    def forward(self,x):
        if self.family=='Transformer':
            tokens=self.projection(x)+self.position[:x.shape[1]].flip(0).unsqueeze(0)
            with sdpa_kernel(SDPBackend.MATH):hidden=self.encoder(tokens)
        else:hidden,_=self.core(x)
        return x[:,-1,self.j:self.j+1]+self.head(self.dropout(hidden[:,-1]))
