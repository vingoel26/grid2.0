#!/usr/bin/env python3
"""Model F — fine-tune MobileNetV3-Small scene classifier (~20 min on Kaggle T4).

ImageFolder layout:
  data/weather/{train,val}/{clear,hazy,rainy,low_light,motion_blur}/*.jpg

Augment 'clear' into low_light (gamma<1) and motion_blur (Gaussian) to balance
classes (Part 5). Produces data/scene_model/best.pt.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import torch
from torch import nn
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms

CLASSES = ["clear", "hazy", "rainy", "low_light", "motion_blur"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/weather")
    ap.add_argument("--out", default="data/scene_model/best.pt")
    ap.add_argument("--epochs", type=int, default=15)
    ap.add_argument("--bs", type=int, default=64)
    args = ap.parse_args()

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    tf = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    tr = DataLoader(datasets.ImageFolder(Path(args.data) / "train", tf), args.bs, shuffle=True)
    va = DataLoader(datasets.ImageFolder(Path(args.data) / "val", tf), args.bs)

    net = models.mobilenet_v3_small(weights="IMAGENET1K_V1")
    net.classifier[-1] = nn.Linear(1024, len(CLASSES))
    net.to(dev)

    opt = torch.optim.AdamW(net.parameters(), lr=1e-3)
    crit = nn.CrossEntropyLoss()

    best = 0.0
    for ep in range(args.epochs):
        net.train()
        for x, y in tr:
            x, y = x.to(dev), y.to(dev)
            opt.zero_grad(); crit(net(x), y).backward(); opt.step()
        net.eval()
        c = t = 0
        with torch.no_grad():
            for x, y in va:
                x, y = x.to(dev), y.to(dev)
                c += (net(x).argmax(1) == y).sum().item(); t += y.numel()
        acc = c / max(t, 1)
        print(f"epoch {ep+1}/{args.epochs}  val_acc={acc:.4f}")
        if acc > best:
            best = acc
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            torch.save(net.state_dict(), args.out)
    print(f"Best val_acc={best:.4f} -> {args.out}")


if __name__ == "__main__":
    main()
