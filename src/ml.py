"""Machine-learning components.

1. Unsupervised anomaly detection (Isolation Forest) -- needs NO labels.
   It flags cropped pixels whose combination of NDVI / NDRE / NDMI (/ LST) is
   statistically unusual compared with the rest of the farm on the same date.
   "Unusual" is not the same as "water stressed"; it is a pointer for inspection.

2. Supervised Random Forest -- ONLY trained if real ground-truth labels exist in
   data/ground_truth/labels.csv. No labels are shipped with this prototype, so
   by default the model is reported as NOT TRAINED. We do not fabricate labels.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler

LABELS_PATH = Path(__file__).resolve().parents[1] / "data" / "ground_truth" / "labels.csv"
CANDIDATE_FEATURES = ["ndvi", "ndre", "ndmi", "lst", "dndvi", "air_temp_c", "precip_mm"]
MIN_ROWS, MIN_PER_CLASS = 30, 5
IF_CONTAMINATION = 0.05  # expected share of unusual pixels -- a model setting, not a finding
IF_N_ESTIMATORS = 200


def isolation_forest(samples: pd.DataFrame, contamination: float = IF_CONTAMINATION) -> tuple[pd.DataFrame, list[str]]:
    feats = [c for c in ("NDVI", "NDRE", "NDMI", "LST") if c in samples and samples[c].notna().mean() > 0.9]
    df = samples.dropna(subset=feats).copy()
    if len(df) < 50 or not feats:
        return pd.DataFrame(), feats
    X = StandardScaler().fit_transform(df[feats].to_numpy())
    model = IsolationForest(n_estimators=IF_N_ESTIMATORS, contamination=contamination, random_state=42)
    df["anomaly"] = model.fit_predict(X) == -1
    df["anomaly_score"] = -model.score_samples(X)
    return df, feats


def assign_zones(pix: pd.DataFrame, zones: pd.DataFrame) -> pd.DataFrame:
    """Attach the zone_id of the grid cell containing each pixel sample (drops samples outside all zones)."""
    lon, lat = pix.lon.to_numpy()[:, None], pix.lat.to_numpy()[:, None]
    inside = (
        (zones.min_lon.to_numpy() <= lon) & (zones.max_lon.to_numpy() >= lon)
        & (zones.min_lat.to_numpy() <= lat) & (zones.max_lat.to_numpy() >= lat)
    )
    zid = np.where(inside.any(axis=1), zones.zone_id.to_numpy()[inside.argmax(axis=1)], None)
    return pix.assign(zone_id=zid).dropna(subset=["zone_id"])


def anomaly_share_by_zone(pix: pd.DataFrame, zones: pd.DataFrame) -> pd.Series:
    if pix.empty:
        return pd.Series(dtype=float)
    return assign_zones(pix, zones).groupby("zone_id")["anomaly"].mean()


def supervised_status() -> dict:
    """Describe whether a supervised model can be trained from real labels."""
    if not LABELS_PATH.exists():
        return {"ready": False, "reason": f"No ground-truth file found at data/ground_truth/labels.csv."}
    df = pd.read_csv(LABELS_PATH)
    feats = [c for c in CANDIDATE_FEATURES if c in df.columns and df[c].notna().mean() > 0.8]
    if "label" not in df.columns or not feats:
        return {"ready": False, "reason": "labels.csv needs a 'label' column and at least one feature column."}
    df = df.dropna(subset=feats + ["label"])
    counts = df["label"].value_counts()
    if len(df) < MIN_ROWS or len(counts) < 2 or counts.min() < MIN_PER_CLASS:
        return {
            "ready": False,
            "reason": f"Only {len(df)} usable labelled rows / {len(counts)} classes "
            f"(need ≥{MIN_ROWS} rows, ≥2 classes, ≥{MIN_PER_CLASS} per class).",
        }
    return {"ready": True, "df": df, "features": feats, "counts": counts}


def train_random_forest(status: dict) -> dict:
    df, feats = status["df"], status["features"]
    X, y = df[feats].to_numpy(), df["label"].astype(str).to_numpy()
    k = int(min(5, status["counts"].min()))
    rf = RandomForestClassifier(n_estimators=300, max_depth=6, random_state=42, class_weight="balanced")
    cv = cross_val_score(rf, X, y, cv=StratifiedKFold(k, shuffle=True, random_state=42), scoring="balanced_accuracy")
    rf.fit(X, y)
    imp = pd.Series(rf.feature_importances_, index=feats).sort_values(ascending=False)
    return {"model": rf, "features": feats, "cv_scores": cv, "importances": imp, "n": len(df), "k": k}


def predict_zones(result: dict, zones: pd.DataFrame) -> pd.Series:
    feats = result["features"]
    ok = zones.dropna(subset=[f for f in feats if f in zones.columns])
    if any(f not in zones.columns for f in feats) or ok.empty:
        return pd.Series(dtype=object)
    return pd.Series(result["model"].predict(ok[feats].to_numpy()), index=ok.zone_id)
