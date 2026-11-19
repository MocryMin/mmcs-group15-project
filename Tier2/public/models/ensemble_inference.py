"""Run the released in-12h-exact ensembles on prepared 24 × 76 features."""
import argparse
import json
import math
from pathlib import Path

import numpy as np
import torch
from safetensors.torch import load_file
from torch import nn
from torch.nn import functional as F

from inference import TransformerForecaster


def read_config(folder):
    return json.loads((folder / "config.json").read_text(encoding="utf-8"))


class LocalTransformer(TransformerForecaster):
    def __init__(self, spec):
        super().__init__(spec, (24, 76))
        self.local = nn.Linear(spec["hidden_width"], 3)

    def forward(self, x):
        z = self.norm(self.seq(self.emb(x) + self.pos))
        return self.out(self.drop(z.mean(1))).reshape(-1, 24, 3) + self.local(self.drop(z))


class Attention(nn.Module):
    def __init__(self, width):
        super().__init__()
        self.qkv = nn.Linear(width, 3 * width)
        self.out = nn.Linear(width, width)

    def forward(self, x):
        n, length, width = x.shape
        q, k, v = (a.reshape(n, length, 4, width // 4).transpose(1, 2)
                   for a in self.qkv(x).chunk(3, dim=-1))
        attended = F.scaled_dot_product_attention(q, k, v)
        return self.out(attended.transpose(1, 2).reshape(n, length, width))


class FeedForward(nn.Module):
    def __init__(self, width):
        super().__init__()
        self.up = nn.Linear(width, 2 * width)
        self.down = nn.Linear(2 * width, width)

    def forward(self, x):
        return self.down(F.gelu(self.up(x)))


class EncoderBlock(nn.Module):
    def __init__(self, width):
        super().__init__()
        self.attn_norm = nn.LayerNorm(width)
        self.attn = Attention(width)
        self.ff_norm = nn.LayerNorm(width)
        self.ff = FeedForward(width)

    def forward(self, x):
        x = x + self.attn(self.attn_norm(x))
        return x + self.ff(self.ff_norm(x))


class ResidualTransformer(nn.Module):
    def __init__(self, spec):
        super().__init__()
        width = spec["hidden_width"]
        self.input = nn.Linear(76, width)
        phase = torch.arange(24, dtype=torch.float32)[:, None] * torch.exp(
            torch.arange(0, width, 2) * (-math.log(10000.0) / width))
        pos = torch.stack((phase.sin(), phase.cos()), dim=-1).flatten(1)
        self.register_buffer("pos", pos, persistent=False)
        self.layers = nn.ModuleList(EncoderBlock(width) for _ in range(spec["layers"]))
        self.norm = nn.LayerNorm(width)
        self.local = nn.Linear(width, 3)
        if spec["readout"] == "local_dct":
            bands = spec["dct_nonconstant_bands"] + 1
            phase = (torch.arange(24)[:, None] + 0.5) * torch.arange(bands) * math.pi / 24
            self.register_buffer("basis", phase.cos(), persistent=False)
            self.fourier_head = nn.Linear(width, 3 * bands)
        else:
            self.global_head = nn.Linear(width, 72)

    def forward(self, x):
        z = self.input(x) + self.pos
        for block in self.layers:
            z = block(z)
        z = self.norm(z)
        local = self.local(z)
        if hasattr(self, "basis"):
            amplitudes = self.fourier_head(z.mean(1)).reshape(-1, self.basis.shape[1], 3)
            return local + torch.einsum("hk,bkt->bht", self.basis, amplitudes)
        return local + self.global_head(z.mean(1)).reshape(-1, 24, 3)


class ExactEnsemble:
    def __init__(self, folder, device="cpu"):
        folder = Path(folder).resolve()
        model_root = folder.parents[1]
        self.config = read_config(folder)
        self.device = torch.device(device)
        baseline = self.config
        if self.config["version"] == 2:
            baseline = read_config(folder.parent / self.config["base_ensemble"])
        self.base_routes = baseline["routes"]
        self.upgrades = self.config["routes"] if self.config["version"] == 2 else []
        self.members = {}
        for route in self.base_routes + self.upgrades:
            member = route["bundle"]
            if member in self.members:
                continue
            path = model_root / member
            spec = read_config(path)
            states = [load_file(path / w["file"], device=str(self.device)) for w in spec["weights"]]
            if spec["family"] == "ridge":
                self.ridge = states[0]
            else:
                architecture = LocalTransformer if spec["kind"] == "local_transformer" else ResidualTransformer
                networks = []
                for state in states:
                    model = architecture(spec["architecture"]).to(self.device)
                    model.load_state_dict(state, strict=True)
                    networks.append(model.eval())
                self.members[member] = (networks, spec["ridge_anchor"])

    @torch.inference_mode()
    def predict(self, x, reference=None):
        values = torch.as_tensor(np.array(x, dtype=np.float32, copy=True), device=self.device)
        if values.ndim != 3 or values.shape[1:] != (24, 76) or not torch.isfinite(values).all():
            raise ValueError("Expected finite standardized features of shape (N, 24, 76).")
        ridge = (values.flatten(1).double() @ self.ridge["weight"] + self.ridge["bias"]).reshape(-1,24,3).float()
        output = torch.empty_like(ridge)
        forecasts = {}
        for route in self.base_routes + self.upgrades:
            name, target = route["bundle"], route["target"]
            start, stop = route["start"], route["stop"]
            if name not in forecasts:
                if name not in self.members:
                    forecasts[name] = ridge
                else:
                    models, anchor = self.members[name]
                    forecasts[name] = torch.stack([model(values) + anchor * ridge for model in models]).double().mean(0)
            forecast = forecasts[name][:, start:stop, target]
            weight = route.get("weight", 1)
            if weight < 1:
                forecast = (1-weight) * output[:, start:stop, target] + weight * forecast
            output[:, start:stop, target] = forecast
        result = output.cpu().numpy()
        if reference is not None:
            center = np.asarray(reference)
            if center.shape != result.shape:
                raise ValueError("Expected a reference array of shape (N, 24, 3).")
            return center + result * np.asarray(self.config["target_sd"])
        return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle")
    parser.add_argument("inputs")
    parser.add_argument("output")
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()
    model = ExactEnsemble(args.bundle, args.device)
    with np.load(args.inputs) as data:
        np.save(args.output, model.predict(data["x"], data["reference"] if "reference" in data else None))
