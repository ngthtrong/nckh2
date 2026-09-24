"""Run a few independent-test images through the letterbox PyTorch pipeline."""

from pathlib import Path

import pandas as pd
import torch
from PIL import Image, ImageOps
from torch import nn
from torchvision import models, transforms


ROOT = Path(__file__).resolve().parents[1]
V2_DIR = ROOT / "model" / "models" / "mobilenetv3_large_relabel_v2"
V2_CHECKPOINT = V2_DIR / "flood_mobilenetv3_large_relabel_v2_best.pth"
V1_CHECKPOINT = (
    ROOT / "model" / "models" / "mobilenetv3_large_relabel"
    / "flood_mobilenetv3_large_relabel_best.pth"
)
SPLIT_CSV = V2_DIR / "split_train_val_test_mobilenetv3_large_v2.csv"


def build_model(num_classes: int, dropout: float) -> nn.Module:
    model = models.mobilenet_v3_large(weights=None)
    classifier = list(model.classifier.children())[:-1]
    in_features = model.classifier[-1].in_features
    model.classifier = nn.Sequential(
        *classifier,
        nn.Sequential(nn.Dropout(dropout), nn.Linear(in_features, num_classes)),
    )
    return model


def main() -> None:
    checkpoint_path = V2_CHECKPOINT if V2_CHECKPOINT.exists() else V1_CHECKPOINT
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    class_order = checkpoint["class_names"]
    model = build_model(len(class_order), float(checkpoint.get("dropout", 0.35)))
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    transform = transforms.Compose([
        transforms.Lambda(lambda image: ImageOps.pad(
            image,
            (224, 224),
            method=Image.Resampling.BICUBIC,
            color=(124, 116, 104),
        )),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])

    split_df = pd.read_csv(SPLIT_CSV)
    samples = split_df[split_df["split"] == "test"].groupby("label", sort=False).head(1).head(3)
    with torch.no_grad():
        for row in samples.itertuples(index=False):
            with Image.open(row.path) as image:
                tensor = transform(image.convert("RGB")).unsqueeze(0)
            probabilities = torch.softmax(model(tensor), dim=1)[0]
            prediction = int(probabilities.argmax())
            print(
                f"{Path(row.path).name}: true={row.label}, "
                f"pred={class_order[prediction]}, confidence={probabilities[prediction]:.4f}, "
                f"input={tuple(tensor.shape)}"
            )

    print(f"checkpoint={checkpoint_path}")
    print("smoke_test=PASS")


if __name__ == "__main__":
    main()
