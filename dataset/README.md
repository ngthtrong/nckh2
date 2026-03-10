# Dataset Workspace

This folder contains the operational dataset workspace for the project.

## Directory layout

- image_data/raw: Raw images before preprocessing.
- image_data/processed/train|val|test/{no_flood,low_flood,high_flood}: Split output for training.
- text_data/raw: Raw text files and source dumps.
- text_data/processed: Processed CSV splits.
- reports: Auto-generated statistics and quality reports.

## Execution order

1. Fill metadata and text templates.
2. Place raw images under image_data/raw grouped by source.
3. Run scripts/prepare_dataset.py for image preprocessing and split.
4. Export text split files to text_data/processed.
5. Update reports in dataset/reports.

## Label schema summary

Image labels:
- no_flood
- low_flood
- high_flood

Text labels:
- urgent_rescue
- need_supplies
- safe_update
- irrelevant
