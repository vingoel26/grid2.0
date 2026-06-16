#!/usr/bin/env python3
"""Model E — fine-tune EfficientNetV2-S helmet classifier (~1 hr on Kaggle T4).

Expects head-crop images in an ImageFolder layout:
  data/helmet/{train,val}/{helmet,no_helmet,ambiguous}/*.jpg

Produces data/helmet_model/best.pt — loaded by ml/models/helmet_classifier.py.
Build the head-crop dataset from SHWD + Kaggle helmet sets (Part 5).
"""
from __future__ import annotations

import argparse
from pathlib import Path

import torch
from torch import nn
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms

CLASSES = ["helmet", "no_helmet", "ambiguous"]


def loaders(root: Path, bs: int):
    train_tf = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(brightness=0.3, contrast=0.2),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    val_tf = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    tr = datasets.ImageFolder(root / "train", train_tf)
    va = datasets.ImageFolder(root / "val", val_tf)
    return (DataLoader(tr, bs, shuffle=True, num_workers=2),
            DataLoader(va, bs, num_workers=2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/helmet")
    ap.add_argument("--out", default="data/helmet_model/best.pt")
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--bs", type=int, default=32)
    args = ap.parse_args()

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    tr, va = loaders(Path(args.data), args.bs)

    net = models.efficientnet_v2_s(weights="IMAGENET1K_V1")
    net.classifier[-1] = nn.Linear(1280, len(CLASSES))
    net.to(dev)

    opt = torch.optim.AdamW(net.parameters(), lr=3e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.epochs)
    crit = nn.CrossEntropyLoss()

    best_acc = 0.0
    for ep in range(args.epochs):
        net.train()
        for x, y in tr:
            x, y = x.to(dev), y.to(dev)
            opt.zero_grad()
            crit(net(x), y).backward()
            opt.step()
        sched.step()

        net.eval()
        correct = total = 0
        with torch.no_grad():
            for x, y in va:
                x, y = x.to(dev), y.to(dev)
                correct += (net(x).argmax(1) == y).sum().item()
                total += y.numel()
        acc = correct / max(total, 1)
        print(f"epoch {ep+1}/{args.epochs}  val_acc={acc:.4f}")
        if acc > best_acc:
            best_acc = acc
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            torch.save(net.state_dict(), args.out)
    print(f"Best val_acc={best_acc:.4f} -> {args.out}")


if __name__ == "__main__":
    main()
