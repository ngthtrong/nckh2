# Dataset Acquisition Summary
**Project**: Edge AI System for Flood Rescue Event Analysis  
**Last Updated**: June 2025

---

## 1. Current Dataset State

### Organized Images (train / val / test)

| Split | no_flood | low_flood | high_flood | Total |
|-------|----------|-----------|------------|-------|
| train | 640      | 1,456     | 596        | 2,692 |
| val   | 80       | 181       | 74         | 335   |
| test  | 80       | 185       | 75         | 340   |
| **Total** | **800** | **1,822** | **745** | **3,367** |

> **All 3,367 images are from STURM-FloodDepth** (source prefix: `sturm_`).

---

## 2. Dataset Sources

### ✅ STURM-FloodDepth (COMPLETE)

| Property | Value |
|----------|-------|
| Source | https://zenodo.org/records/14833532 |
| License | CC BY 4.0 |
| Size | ~168 MB (167.6 MB ZIP downloaded) |
| Images | 3,779 raw → **3,367 organized** |
| Subject | Flooded vehicles in urban environments |
| Labels | 5-level flood depth (Level 0–4) |
| Split used | Official train/val/test splits |

**Level → class mapping:**
- Level0 → `no_flood`  
- Level1, Level2 → `low_flood`  
- Level3, Level4 → `high_flood`

**Raw files:** `dataset/image_data/raw/sturm_flood_depth/upscaled_images/Level0-4/`  
**Split files:** `dataset/image_data/raw/sturm_flood_depth/train.txt`, `val.txt`, `test.txt`  
**Organization script:** `scripts/organize_sturm_dataset.py` ✅ Tested

---

### ⏳ CrisisMMD v2.0 (ANNOTATIONS READY — IMAGES PENDING)

| Property | Value |
|----------|-------|
| Source | https://crisisnlp.qcri.org/crisismmd |
| License | Research use (cite paper) |
| Images | ~1.8 GB (user downloading manually) |
| Subject | Multi-disaster social media images (hurricanes, floods, etc.) |
| Labels | severe_damage / mild_damage / little_or_no_damage / not_humanitarian |
| Splits | Using `task_damage_text_img_*.tsv` in `all` version |

**Annotation files extracted to:** `dataset/image_data/raw/crisismmd_annotations/`

**Label → class mapping:**
- `severe_damage` → `high_flood`  
- `mild_damage` → `low_flood`  
- `little_or_no_damage` → `no_flood`  
- `not_humanitarian` → **SKIP**

**Label distribution in annotations:**

| Split | severe_damage → high_flood | mild_damage → low_flood | little_or_no_damage → no_flood | Total |
|-------|---------------------------|------------------------|-------------------------------|-------|
| train | 1,548 | 587 | 333 | 2,468 |
| dev   | 332   | 126 | 71  | 529   |
| test  | 332   | 126 | 71  | 529   |

**To run after downloading images:**
1. Place CrisisMMD images in: `dataset/image_data/raw/crisismmd/`  
   *(The TSV `image` column uses paths like `data_image/hurricane_harvey/8_9_2017/<tweet_id>_0.jpg` — place the full `data_image/` folder inside `raw/crisismmd/`)*
2. Run: `C:\Python313\python.exe scripts\organize_crisismmd_dataset.py`

**Organization script:** `scripts/organize_crisismmd_dataset.py` ✅ Created (not yet tested)

---

### ❌ Wikimedia Commons (BLOCKED — RATE LIMITED)

**Script:** `scripts/download_wikimedia_flood.py`  
**Status:** HTTP 429 rate limit — needs multi-hour cooldown before retry  
**Categories targetted:** `Floods_in_Vietnam`, `2020_floods_in_Vietnam`, `Effects_of_Hurricane_Harvey_in_Texas`  
**Action:** Wait for rate limit reset, then re-run the script

---

### ❌ DVIDS (Defense Visual Information Distribution Service)

**URL:** `https://api.dvidshub.net/v2/media/search`  
**Status:** HTTP 403 Forbidden — requires API key authentication  
**Workaround:** Visit https://www.dvidshub.net/ manually and download flood images, place in `dataset/image_data/raw/dvids/`

---

### ❌ FloodNet (MANUAL DOWNLOAD REQUIRED)

| Property | Value |
|----------|-------|
| Source | https://github.com/BinaLab/FloodNet-Supervised_v1.0 |
| Size | ~2 GB |
| Images | ~2,343 UAS (drone) aerial images |
| Labels | 10 semantic classes (road, building, flood, etc.) |
| Access | Dropbox or Google Drive link (requires account) |

**Note:** FloodNet has 10 semantic segmentation classes. For this project, relevant remapping:
- `flooded-road`, `flooded-building` → `high_flood`  
- `non-flooded-road`, `non-flooded-building` → `low_flood` or `no_flood`

---

## 3. Estimated Dataset After CrisisMMD Integration

| Split | no_flood | low_flood | high_flood | Total |
|-------|----------|-----------|------------|-------|
| train | ~973     | ~2,043    | ~2,144     | ~5,160 |
| val   | ~151     | ~307      | ~406       | ~864  |
| test  | ~151     | ~311      | ~407       | ~869  |
| **Total** | **~1,275** | **~2,661** | **~2,957** | **~6,893** |

> Note: CrisisMMD dev → project val, CrisisMMD test → project test. Images classified as `not_humanitarian` are skipped.

---

## 4. Class Imbalance Analysis

### Current (STURM only)
| Class | Count | % |
|-------|-------|---|
| no_flood | 800 | 23.7% |
| low_flood | 1,822 | 54.1% |
| high_flood | 745 | 22.2% |

**Concern:** `no_flood` is underrepresented.

### After CrisisMMD
| Class | Count | % |
|-------|-------|---|
| no_flood | ~1,275 | 18.5% |
| low_flood | ~2,661 | 38.6% |
| high_flood | ~2,957 | 42.9% |

**Concern:** `no_flood` is still the least-represented class.

### Mitigation Strategies
1. **Weighted loss** during training: `class_weight = {no_flood: 3.0, low_flood: 1.0, high_flood: 1.2}`
2. **Data augmentation** (flips, brightness, rotation) applied more aggressively to `no_flood`
3. **Additional no_flood sources to consider:**
   - ImageNet car/street subsets (pre-flood urban imagery)
   - Wikimedia `normal_street_images` categories (when rate limit lifts)

---

## 5. Suggested Additional Free Datasets

| Dataset | URL | Notes |
|---------|-----|-------|
| FloodNet | https://github.com/BinaLab/FloodNet-Supervised_v1.0 | ~2GB, Dropbox link, manual |
| NOAA Flood Archive | https://www.nssl.noaa.gov/projects/flash/data/ | Public domain weather photos |
| ERC Flood Photos | https://www.rccc.eu/gallery | Manual download |
| ReliefWeb | https://reliefweb.int/ | Humanitarian flood images |
| USGS Stream Photos | https://waterdata.usgs.gov/ | Some flood event imagery |
| GitHub `flood-dataset` topic | https://github.com/topics/flood-dataset | Search for open image collections |
| Open Images V7 (Google) | https://storage.googleapis.com/openimages/web/index.html | Filter by "Flood" entity |

---

## 6. File Organization

```
dataset/image_data/
├── raw/
│   ├── sturm_flood_depth/          ✅ Downloaded & extracted
│   │   ├── upscaled_images/
│   │   │   └── Level0/, Level1/, Level2/, Level3/, Level4/
│   │   ├── train.txt
│   │   ├── val.txt
│   │   └── test.txt
│   ├── crisismmd_annotations/      ✅ Annotation TSVs ready
│   │   ├── all/crisismmd_datasplit_all/*.tsv
│   │   └── agreed/crisismmd_datasplit_agreed_label/*.tsv
│   └── crisismmd/                  ⏳ PLACE USER-DOWNLOADED IMAGES HERE
│       └── data_image/             (extract the CrisisMMD ZIP here)
├── train/
│   ├── no_flood/    (640 STURM images)
│   ├── low_flood/   (1,456 STURM images)
│   └── high_flood/  (596 STURM images)
├── val/
│   ├── no_flood/    (80)
│   ├── low_flood/   (181)
│   └── high_flood/  (74)
└── test/
    ├── no_flood/    (80)
    ├── low_flood/   (185)
    └── high_flood/  (75)
```

---

## 7. Scripts Reference

| Script | Purpose | Status |
|--------|---------|--------|
| `scripts/organize_sturm_dataset.py` | Organize STURM Level0-4 → 3-class train/val/test | ✅ Tested |
| `scripts/organize_crisismmd_dataset.py` | Organize CrisisMMD images → 3-class (run after download) | ✅ Created |
| `scripts/download_wikimedia_flood.py` | Download Wikimedia flood category images | ⚠️ Rate limited |
| `scripts/download_fema_flood.py` | Download FEMA/public domain flood images | ⚠️ Rate limited |

---

## 8. Next Steps

- [ ] User completes manual CrisisMMD v2.0 image download
- [ ] Place CrisisMMD images at `dataset/image_data/raw/crisismmd/data_image/`
- [ ] Run `organize_crisismmd_dataset.py` to merge into train/val/test
- [ ] Retry Wikimedia download script after rate limit clears (wait ≥2 hours)
- [ ] Consider FloodNet for aerial/UAS perspective diversity
- [ ] Add class-weighting to training config to address no_flood imbalance
- [ ] Generate final dataset statistics after all sources integrated
