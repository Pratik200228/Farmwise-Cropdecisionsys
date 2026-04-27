"""
Layer 3: Unified plant disease fine-tuning pipeline.

Fine-tunes a MobileNetV2 backbone on one or more plant disease datasets
(PlantVillage by default, optionally extended with PlantDoc / rice / wheat /
mustard etc.) and saves a single checkpoint that the backend health agent
can swap into. The output covers all your major crops in one model.

Usage examples (run from the `backend/` folder, after activating .venv):

    python scripts/train_unified_disease_model.py \\
        --datasets mohanty/PlantVillage \\
        --output app/models/unified_plant_disease.pth \\
        --epochs 8 --batch-size 32

    python scripts/train_unified_disease_model.py \\
        --datasets mohanty/PlantVillage,wambugu71/CropDiseaseDetection \\
        --epochs 12 --batch-size 64 --image-size 224

Hardware notes:
    * CPU only:  ~2-4 hours for 1 epoch on PlantVillage (~54k images).
    * Single GPU (T4/RTX 3060): ~6-12 minutes per epoch.
    * 8-12 epochs is usually plenty when fine-tuning from ImageNet.

Dataset notes:
    * `mohanty/PlantVillage` (Hugging Face Hub) needs `datasets` lib.
    * Local folder layout is also supported via `--datasets path/to/dir`
      where the folder contains class-named subfolders (ImageFolder format).
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import List, Tuple

import torch
from torch import nn, optim
from torch.utils.data import DataLoader, ConcatDataset, random_split
from torchvision import datasets as tvdatasets
from torchvision import models, transforms


def _build_transforms(image_size: int) -> Tuple[transforms.Compose, transforms.Compose]:
    train_tfm = transforms.Compose([
        transforms.Resize((image_size + 16, image_size + 16)),
        transforms.RandomCrop((image_size, image_size)),
        transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    eval_tfm = transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    return train_tfm, eval_tfm


def _load_dataset(spec: str, train_tfm, eval_tfm):
    """Return (dataset, class_names) for either a HF Hub spec or a local folder.

    Local folders use `torchvision.datasets.ImageFolder` directly.
    HF Hub specs are loaded via `datasets.load_dataset` and wrapped in a
    thin torch dataset that yields (PIL image, label).
    """
    spec = spec.strip()
    if os.path.isdir(spec):
        ds = tvdatasets.ImageFolder(spec, transform=train_tfm)
        return ds, ds.classes

    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise SystemExit(
            "The `datasets` library is required for HF Hub datasets. "
            "Install it with: pip install datasets"
        ) from exc

    print(f"[load] downloading HF dataset: {spec}")
    hf = load_dataset(spec, split="train")
    if "label" not in hf.features:
        raise SystemExit(f"Dataset {spec} has no `label` feature.")
    class_names = hf.features["label"].names

    class _HFWrapped(torch.utils.data.Dataset):
        def __init__(self, ds, tfm):
            self.ds = ds
            self.tfm = tfm
        def __len__(self):
            return len(self.ds)
        def __getitem__(self, i):
            row = self.ds[i]
            img = row["image"].convert("RGB")
            return self.tfm(img), int(row["label"])

    return _HFWrapped(hf, train_tfm), class_names


def _build_model(num_classes: int, freeze_features: bool) -> nn.Module:
    net = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.IMAGENET1K_V2)
    if freeze_features:
        for p in net.features.parameters():
            p.requires_grad = False
    in_features = net.classifier[1].in_features
    net.classifier[1] = nn.Sequential(
        nn.Dropout(0.2),
        nn.Linear(in_features, num_classes),
    )
    return net


def _train_one_epoch(net, loader, criterion, optimizer, device) -> Tuple[float, float]:
    net.train()
    total, correct, loss_sum = 0, 0, 0.0
    for batch_idx, (x, y) in enumerate(loader):
        x = x.to(device, non_blocking=True)
        y = y.to(device, non_blocking=True)
        logits = net(x)
        loss = criterion(logits, y)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        loss_sum += loss.item() * x.size(0)
        total += x.size(0)
        correct += (logits.argmax(1) == y).sum().item()
        if batch_idx % 50 == 0:
            print(f"   batch {batch_idx:>5}  loss={loss.item():.4f}  running_acc={correct/total:.3f}")
    return loss_sum / max(total, 1), correct / max(total, 1)


@torch.no_grad()
def _evaluate(net, loader, criterion, device) -> Tuple[float, float]:
    net.eval()
    total, correct, loss_sum = 0, 0, 0.0
    for x, y in loader:
        x = x.to(device, non_blocking=True)
        y = y.to(device, non_blocking=True)
        logits = net(x)
        loss = criterion(logits, y)
        loss_sum += loss.item() * x.size(0)
        total += x.size(0)
        correct += (logits.argmax(1) == y).sum().item()
    return loss_sum / max(total, 1), correct / max(total, 1)


def main():
    parser = argparse.ArgumentParser(description="Unified plant disease fine-tune")
    parser.add_argument("--datasets", default="mohanty/PlantVillage",
                        help="Comma-separated list of HF dataset IDs or local ImageFolder paths.")
    parser.add_argument("--output", default="app/models/unified_plant_disease.pth")
    parser.add_argument("--classes-output", default="app/models/unified_class_names.json")
    parser.add_argument("--image-size", type=int, default=224)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--val-split", type=float, default=0.1)
    parser.add_argument("--freeze-features", action="store_true",
                        help="Freeze MobileNetV2 backbone (faster, slightly lower accuracy).")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    torch.manual_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[env] device={device}  torch={torch.__version__}")

    train_tfm, eval_tfm = _build_transforms(args.image_size)

    datasets_combined: List[torch.utils.data.Dataset] = []
    all_classes: List[str] = []
    label_offset = 0
    for spec in [s for s in args.datasets.split(",") if s.strip()]:
        ds, classes = _load_dataset(spec, train_tfm, eval_tfm)
        if not all_classes:
            all_classes = list(classes)
        else:
            # Re-map labels from this dataset's local space to the combined one.
            class _Remapped(torch.utils.data.Dataset):
                def __init__(self, base, mapping):
                    self.base = base
                    self.mapping = mapping
                def __len__(self):
                    return len(self.base)
                def __getitem__(self, i):
                    x, y = self.base[i]
                    return x, self.mapping[y]

            mapping = {}
            for local_idx, name in enumerate(classes):
                if name in all_classes:
                    mapping[local_idx] = all_classes.index(name)
                else:
                    mapping[local_idx] = len(all_classes)
                    all_classes.append(name)
            ds = _Remapped(ds, mapping)
        datasets_combined.append(ds)
        print(f"[load] {spec}  size={len(ds)}  total_classes_so_far={len(all_classes)}")
        label_offset += 1

    full = ConcatDataset(datasets_combined) if len(datasets_combined) > 1 else datasets_combined[0]
    n_total = len(full)
    n_val = max(int(n_total * args.val_split), 1)
    n_train = n_total - n_val
    train_set, val_set = random_split(
        full, [n_train, n_val],
        generator=torch.Generator().manual_seed(args.seed),
    )
    print(f"[split] train={n_train}  val={n_val}  classes={len(all_classes)}")

    train_loader = DataLoader(
        train_set, batch_size=args.batch_size, shuffle=True,
        num_workers=args.workers, pin_memory=(device.type == "cuda"),
    )
    val_loader = DataLoader(
        val_set, batch_size=args.batch_size, shuffle=False,
        num_workers=args.workers, pin_memory=(device.type == "cuda"),
    )

    net = _build_model(len(all_classes), freeze_features=args.freeze_features).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(filter(lambda p: p.requires_grad, net.parameters()), lr=args.lr)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    best_acc = 0.0
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    for epoch in range(1, args.epochs + 1):
        t0 = time.time()
        print(f"\n=== epoch {epoch}/{args.epochs} ===")
        train_loss, train_acc = _train_one_epoch(net, train_loader, criterion, optimizer, device)
        val_loss, val_acc = _evaluate(net, val_loader, criterion, device)
        scheduler.step()
        elapsed = time.time() - t0
        print(f"[epoch {epoch}] train_loss={train_loss:.4f} train_acc={train_acc:.3f} "
              f"| val_loss={val_loss:.4f} val_acc={val_acc:.3f}  ({elapsed:.0f}s)")

        if val_acc > best_acc:
            best_acc = val_acc
            torch.save(net.state_dict(), out_path)
            with open(args.classes_output, "w", encoding="utf-8") as f:
                json.dump(all_classes, f, indent=2)
            print(f"[ckpt] saved best to {out_path} ({best_acc:.3f}) and classes to {args.classes_output}")

    print(f"\nDone. best val acc = {best_acc:.3f}.  Checkpoint: {out_path}")
    print("Next: update health_agent.py to load this checkpoint and use the unified class list.")


if __name__ == "__main__":
    main()
