import os, torch, torch.nn as nn, numpy as np
from typing import Dict

class TinyVisionNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(3, 4, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((1,1)),
            nn.Flatten(),
            nn.Linear(4, 1),
            nn.Sigmoid()
        )
    def forward(self, x):
        return self.net(x)

class TinyAudioNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(128, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )
    def forward(self, x):
        return self.net(x)

def pseudo_image_score(filepath: str) -> float:
    # Derive a deterministic pseudo-score from file bytes to keep demos stable
    h = 0
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            h = (h * 1315423911 + sum(chunk)) & 0xffffffff
    rng = np.random.default_rng(h)
    return float(rng.random())  # 0..1

def pseudo_audio_score(filepath: str) -> float:
    h = 0
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            h = (h * 2654435761 + sum(chunk)) & 0xffffffff
    rng = np.random.default_rng(h)
    return float(rng.random())

def pseudo_video_score(filepath: str) -> float:
    h = 0
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            h = (h * 1103515245 + sum(chunk)) & 0xffffffff
    rng = np.random.default_rng(h)
    return float(rng.random())

def metrics_stub() -> Dict:
    # Placeholder metrics demonstrating structure
    return {
        "vision": {"accuracy": 0.91, "auc": 0.95, "f1": 0.89, "version": "vision_v0"},
        "audio":  {"accuracy": 0.88, "auc": 0.93, "f1": 0.86, "version": "audio_v0"},
        "video":  {"accuracy": 0.90, "auc": 0.94, "f1": 0.88, "version": "video_v0"},
        "calibration": {"ece": 0.03}
    }
