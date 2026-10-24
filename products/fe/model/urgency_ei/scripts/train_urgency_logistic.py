#!/usr/bin/env python
import argparse, csv, json, hashlib
from pathlib import Path
import numpy as np
from sklearn.linear_model import LogisticRegression

FEATURES=[
    "unresponsive",
    "respiratory_distress_or_cyanosis",
    "heavy_bleeding",
    "active_convulsions",
    "high_risk_trauma",
]
TARGET="urgency_label"

def load_validate(path):
    with open(path,"r",encoding="utf-8-sig",newline="") as f:
        rows=list(csv.DictReader(f))
    expected=["profile_id"]+FEATURES+[TARGET]
    if not rows or list(rows[0].keys()) != expected:
        raise ValueError(f"Expected exact columns {expected}")
    seen=set()
    for i,r in enumerate(rows,start=2):
        profile=tuple(int(r[f]) for f in FEATURES)
        if profile in seen:
            raise ValueError(f"Duplicate feature profile at CSV row {i}: {profile}")
        seen.add(profile)
        for c in FEATURES+[TARGET]:
            if r[c] not in {"0","1"}:
                raise ValueError(f"Row {i}: {c} must be 0/1")
        expected_label=int(any(int(r[f]) for f in FEATURES))
        if int(r[TARGET]) != expected_label:
            raise ValueError(f"Row {i}: label inconsistent with documented reduced mapping")
    if len(rows)!=32 or len(seen)!=32:
        raise ValueError("Final source-aligned table must contain all 32 unique 2^5 profiles.")
    return rows

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--dataset",default="data/urgency_training_SOURCE_FINAL.csv")
    ap.add_argument("--output",default="model/urgency_logistic_SOURCE_FINAL.json")
    args=ap.parse_args()

    rows=load_validate(args.dataset)
    X=np.array([[int(r[f]) for f in FEATURES] for r in rows],dtype=float)
    y=np.array([int(r[TARGET]) for r in rows],dtype=int)

    model=LogisticRegression(
        solver="liblinear",
        C=1.0,
        class_weight="balanced",
        max_iter=2000,
        random_state=20260928,
    )
    model.fit(X,y)

    p=model.predict_proba(X)[:,1]
    pred=(p>=0.5).astype(int)
    artifact={
        "schema_version":"1.0",
        "model_type":"logistic_regression",
        "dataset_sha256":hashlib.sha256(Path(args.dataset).read_bytes()).hexdigest(),
        "feature_order":FEATURES,
        "intercept":float(model.intercept_[0]),
        "coefficients":{f:float(c) for f,c in zip(FEATURES,model.coef_[0])},
        "threshold":0.5,
        "class_weight":"balanced",
        "training_rows":len(rows),
        "unique_feature_profiles":len(rows),
        "full_protocol_state_fidelity_at_0_5":float((pred==y).mean()),
        "negative_probability":float(p[y==0][0]),
        "minimum_positive_probability":float(p[y==1].min()),
        "output_semantics":"E_i is a guideline-derived mapped-high-acuity evidence score; not a clinically calibrated probability.",
        "claim_boundary":"No expert labels; not full WHO/IITT triage; no clinical or field-validity claim.",
    }
    Path(args.output).parent.mkdir(parents=True,exist_ok=True)
    Path(args.output).write_text(json.dumps(artifact,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps(artifact,indent=2,ensure_ascii=False))

if __name__=="__main__":
    main()
