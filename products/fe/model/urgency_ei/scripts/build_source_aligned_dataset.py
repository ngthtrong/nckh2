#!/usr/bin/env python
"""Build the final source-aligned training table deterministically.

No LLM, free-form scenario generation, random sampling, or copied real-patient data
is used. The table is the complete 2^5 Boolean state space of five selected,
source-mapped WHO-IITT high-acuity signs.
"""
import csv, itertools
from pathlib import Path

FEATURES = [
    "unresponsive",
    "respiratory_distress_or_cyanosis",
    "heavy_bleeding",
    "active_convulsions",
    "high_risk_trauma",
]

def build(output_path):
    rows=[]
    for idx,bits in enumerate(itertools.product([0,1], repeat=len(FEATURES)), start=1):
        state=dict(zip(FEATURES,bits))
        label=int(any(state.values()))
        rows.append({
            "profile_id":f"src-v5-{idx:03d}",
            **state,
            "urgency_label":label,
        })
    out=Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    cols=["profile_id"]+FEATURES+["urgency_label"]
    with out.open("w", newline="", encoding="utf-8-sig") as f:
        w=csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    return rows

if __name__=="__main__":
    build("data/urgency_training_SOURCE_FINAL.csv")
