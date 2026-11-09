"""
ml/train_anomaly_model.py
===========================
STEP (after ml/create_features.py).

Trains an unsupervised Isolation Forest on the engineered flight
features, to flag flights whose overall sensor behaviour looks
statistically unusual - independent of whether we can name the exact
fault (that's the separate classifier in ml/train_fault_model.py).

MISSING-VALUE HANDLING (documented, see also feature_engineering.py):
  - Feature columns that are NaN for EVERY flight (i.e. the underlying
    sensor parameter has no verified column mapping) are dropped
    entirely before training - keeping them would just add constant-
    zero noise dimensions.
  - Any remaining sporadic NaNs (a handful of flights with too little
    valid data for one channel) are filled with that column's median
    across the training set.
  - The final list of feature columns is saved to models/feature_columns.json
    and is exactly what app/services/inference_utils.py uses to build
    the feature vector for a live prediction - so training and inference
    always agree on which columns exist and in what order.

USAGE:

    python ml/train_anomaly_model.py
    python ml/train_anomaly_model.py --contamination 0.1
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from app.config import settings

NON_FEATURE_COLUMNS = {
    "flight_id", "label", "before_after", "date_diff", "flight_length",
    "hierarchy", "fold", "class", "target_class", "hclass", "number_flights_before",
}


def load_features() -> pd.DataFrame:
    path = settings.FEATURES_DIR / "flight_features.csv"
    if not path.exists():
        print(f"[error] {path} not found. Run ml/create_features.py first.")
        sys.exit(1)
    return pd.read_csv(path)


def main():
    parser = argparse.ArgumentParser(description="Train the Isolation Forest anomaly detection model.")
    parser.add_argument("--contamination", type=str, default="auto",
                         help="'auto' or a float 0-0.5, expected proportion of anomalous flights")
    parser.add_argument("--n-estimators", type=int, default=200)
    args = parser.parse_args()
    contamination = "auto" if args.contamination == "auto" else float(args.contamination)

    df = load_features()
    print(f"Loaded feature table: {df.shape}")

    candidate_columns = [c for c in df.columns if c not in NON_FEATURE_COLUMNS]

    fully_empty = [c for c in candidate_columns if df[c].isna().all()]
    feature_columns = [c for c in candidate_columns if c not in fully_empty]
    print(f"Dropping {len(fully_empty)} fully-empty feature columns (unmapped sensors): {fully_empty}")
    print(f"Training on {len(feature_columns)} feature columns.")

    X_df = df[feature_columns].copy()
    sporadic_nan_cols = [c for c in feature_columns if X_df[c].isna().any()]
    if sporadic_nan_cols:
        print(f"Filling sporadic NaNs (median imputation) in {len(sporadic_nan_cols)} columns.")
    for c in sporadic_nan_cols:
        X_df[c] = X_df[c].fillna(X_df[c].median())

    X = X_df.values.astype(np.float64)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    print(f"Training IsolationForest(n_estimators={args.n_estimators}, contamination={contamination})...")
    model = IsolationForest(
        n_estimators=args.n_estimators,
        contamination=contamination,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_scaled)

    predictions = model.predict(X_scaled)  # -1 = anomaly, 1 = normal
    anomaly_fraction = float((predictions == -1).mean())
    print(f"Fraction of TRAINING flights flagged anomalous: {anomaly_fraction:.3f}")

    settings.MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, settings.ANOMALY_MODEL_PATH)
    joblib.dump(scaler, settings.SCALER_PATH)
    with open(settings.FEATURE_COLUMNS_PATH, "w", encoding="utf-8") as f:
        json.dump(feature_columns, f, indent=2)

    metrics = {}
    if settings.METRICS_PATH.exists():
        with open(settings.METRICS_PATH, "r", encoding="utf-8") as f:
            metrics = json.load(f)
    metrics["anomaly_model"] = {
        "n_estimators": args.n_estimators,
        "contamination": contamination,
        "training_flights": len(df),
        "feature_columns": len(feature_columns),
        "training_anomaly_fraction": anomaly_fraction,
        "note": "IsolationForest is unsupervised - this fraction is a training-set diagnostic, "
                "not a validated accuracy metric. See ml/evaluate_models.py for a supervised sanity check.",
    }
    with open(settings.METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print(f"\nSaved:\n  {settings.ANOMALY_MODEL_PATH}\n  {settings.SCALER_PATH}\n  {settings.FEATURE_COLUMNS_PATH}")
    print("\nNote: this scaler.pkl and feature_columns.json are SHARED with the fault classifier "
          "(ml/train_fault_model.py) - run that script next; it will overwrite these two files "
          "with an equivalent (same feature columns) scaler fit the same way, so either training "
          "order works, but re-run both if you change create_features.py's feature set.")
    print("\nNext step: python ml/train_fault_model.py")


if __name__ == "__main__":
    main()
