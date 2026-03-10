# Run Dataset Pipeline

## 1) Fill templates

1. Fill dataset/metadata_template.csv with real image rows.
2. Fill dataset/text_data/rescue_text_samples_template.csv with labeled text rows.
3. Save filled files as:
- dataset/metadata.csv
- dataset/text_data/rescue_text_samples.csv

## 2) Install minimal dependencies

```bash
pip install pillow
```

## 3) Run image preparation

```bash
python scripts/prepare_image_dataset.py \
  --repo-root . \
  --metadata dataset/metadata.csv \
  --output-dir dataset/image_data/processed \
  --image-size 224 \
  --seed 42
```

Outputs:
- dataset/reports/image_split_manifest.csv
- dataset/reports/image_stats.md
- dataset/image_data/processed/train|val|test/...

## 4) Run text preparation

```bash
python scripts/prepare_text_dataset.py \
  --repo-root . \
  --input-csv dataset/text_data/rescue_text_samples.csv \
  --output-dir dataset/text_data/processed \
  --seed 42
```

Outputs:
- dataset/text_data/processed/train.csv
- dataset/text_data/processed/val.csv
- dataset/text_data/processed/test.csv
- dataset/reports/text_stats.md

## 5) Update report template

Update dataset/reports/dataset_report_template.md with final counts and QA metrics.
