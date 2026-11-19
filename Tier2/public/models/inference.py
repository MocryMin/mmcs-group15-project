"""Local inference for the released Tier 2B safetensors bundles.

Usage: python inference.py BUNDLE INPUT.npz OUTPUT.npy
INPUT.npz contains standardized (N, 24, 59) features in 'x' and
physical seasonal reference paths in 'reference' with shape (N, 24, 3).
"""
import argparse
import json
from pathlib import Path

import numpy as np
import torch
from safetensors.torch import load_file
from torch import nn


class TransformerForecaster(nn.Module):
    def __init__(self, spec, shape):
        super().__init__()
        width = spec['hidden_width']
        self.emb = nn.Linear(shape[1], width)
        self.register_buffer('pos', torch.zeros(shape[0], width))
        self.seq = nn.Sequential(*[
            nn.TransformerEncoderLayer(
                width, spec['attention_heads'], spec['feedforward_width'], spec['dropout'],
                'gelu', batch_first=True, norm_first=True,
            ) for _ in range(spec['layers'])
        ])
        self.norm = nn.LayerNorm(width)
        self.drop = nn.Dropout(spec['dropout'])
        self.out = nn.Linear(width, 72)

    def forward(self, x):
        hidden = self.norm(self.seq(self.emb(x) + self.pos)).mean(1)
        return self.out(self.drop(hidden)).reshape(-1, 24, 3)


class RidgeForecaster(nn.Module):
    def __init__(self, shape):
        super().__init__()
        self.weight = nn.Parameter(torch.zeros(shape[0] * shape[1], 72, dtype=torch.float64))
        self.bias = nn.Parameter(torch.zeros(72, dtype=torch.float64))

    def forward(self, x):
        return (x.flatten(1) @ self.weight + self.bias).reshape(-1, 24, 3)


def load_bundle(path, device='cpu'):
    bundle = Path(path)
    config = json.loads((bundle / 'config.json').read_text(encoding='utf-8'))
    architecture, shape = config['architecture'], config['input']['shape']
    if architecture['family'] == 'transformer':
        model = TransformerForecaster(architecture, shape)
    elif architecture['family'] == 'ridge':
        model = RidgeForecaster(shape)
    else:
        raise ValueError(f"Unsupported architecture {architecture['family']}")
    model.load_state_dict(load_file(bundle / 'model.safetensors'), strict=True)
    return model.to(device).eval(), config


def standardize(raw, feature_contract):
    """Transform already constructed columns, using the trained order and scale."""
    values = np.asarray(raw, dtype=np.float32)
    mean = np.asarray(feature_contract['mean'], dtype=np.float64)
    std = np.asarray(feature_contract['std'], dtype=np.float64)
    if values.shape[-1] != len(mean):
        raise ValueError('Incorrect number of feature columns')
    return np.where(np.isfinite(values), (values - mean) / std, 0).astype(np.float32)


@torch.inference_mode()
def forecast(model, config, x, reference=None):
    values = np.asarray(x)
    if values.ndim != 3 or list(values.shape[1:]) != config['input']['shape']:
        raise ValueError('Expected standardized input with shape (N, 24, 59)')
    if not values.flags.writeable:
        values = values.copy()
    parameter = next(model.parameters())
    output = model(torch.as_tensor(values, dtype=parameter.dtype, device=parameter.device)).cpu().numpy()
    if reference is not None:
        reference = np.asarray(reference)
        if reference.shape != output.shape:
            raise ValueError('Expected the physical reference path with shape (N, 24, 3)')
        output = reference + output * np.asarray(config['output']['training_std'])
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bundle')
    parser.add_argument('inputs')
    parser.add_argument('output')
    args = parser.parse_args()
    model, config = load_bundle(args.bundle)
    with np.load(args.inputs) as data:
        np.save(args.output, forecast(model, config, data['x'], data['reference']))
