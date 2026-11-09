"""
ml/evaluate_models.py
=======================
STEP (after both train_anomaly_model.py and train_fault_model.py).

Loads the saved models and the feature table, and prints/saves a combined
evaluation report:

  - Fault classifier: reloads the test-set metrics saved during training
    (models/metrics.json) and re-prints them.
  - Anomaly model: since IsolationForest is unsupervised, we can't
    report "accuracy" honestly. Instead we report a diagnostic
    cross-check: of the flights with a REAL fault label (not "normal"),
    what fraction did the anomaly model flag as anomalous? And of the
    flights labelled "normal", what fraction did it (wrongly) flag?
    This is useful signal for your report, but is NOT the same as a
    validated precision/recall number for a supervised model.

USAGE:

    python ml/evaluate_models.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import joblib
import numpy as np
import pandas as pd

from app.config import settings


def load_features() -> pd.DataFrame:
    path = settings.FEATURES_DIR / "flight_features.csv"
    if not path.exists():
        print(f"[error] {path} not found. Run ml/create_features.py first.")
        sys.exit(1)
    return pd.read_csv(path)


def section(title):
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def main():
    if not settings.FEATURE_COLUMNS_PATH.exists():
        print("[error] models/feature_columns.json not found. Train the models first:\n"
              "  python ml/train_anomaly_model.py\n  python ml/train_fault_model.py")
        sys.exit(1)

    with open(settings.FEATURE_COLUMNS_PATH, "r", encoding="utf-8") as f:
        feature_columns = json.load(f)

    df = load_features()
    X_df = df[feature_columns].copy()
    for c in feature_columns:
        if X_df[c].isna().any():
            X_df[c] = X_df[c].fillna(X_df[c].median())
    X = X_df.values.astype(np.float64)

    scaler = joblib.load(settings.SCALER_PATH) if settings.SCALER_PATH.exists() else None
    X_scaled = scaler.transform(X) if scaler is not None else X

    section("FAULT CLASSIFIER (from models/metrics.json, saved during training)")
    if settings.METRICS_PATH.exists():
        with open(settings.METRICS_PATH, "r", encoding="utf-8") as f:
            metrics = json.load(f)
        fm = metrics.get("fault_model")
        if fm:
            print(f"target column: {fm['target_column']}")
            print(f"model: {fm['model']}")
            print(f"test accuracy: {fm['test_accuracy']:.3f}")
            print(f"test macro F1: {fm['test_macro_f1']:.3f}")
            print(f"classes ({len(fm['classes'])}): {fm['classes']}")
        else:
            print("No fault_model metrics found - run ml/train_fault_model.py.")

        am = metrics.get("anomaly_model")
        if am:
            section("ANOMALY MODEL - training-set diagnostic (saved during training)")
            print(f"n_estimators: {am['n_estimators']}   contamination: {am['contamination']}")
            print(f"training flights flagged anomalous: {am['training_anomaly_fraction']:.3f}")
    else:
        print("No models/metrics.json found - train the models first.")

    section("ANOMALY MODEL vs REAL LABELS - cross-check diagnostic (not a formal accuracy metric)")
    if settings.ANOMALY_MODEL_PATH.exists() and "label" in df.columns:
        anomaly_model = joblib.load(settings.ANOMALY_MODEL_PATH)
        predictions = anomaly_model.predict(X_scaled)  # -1 anomaly, 1 normal
        is_anomaly = predictions == -1
        has_real_fault = df["label"].notna() & (df["label"].astype(str).str.lower() != "normal")

        flagged_among_faulty = is_anomaly[has_real_fault.values].mean() if has_real_fault.any() else float("nan")
        flagged_among_normal = is_anomaly[~has_real_fault.values].mean() if (~has_real_fault).any() else float("nan")

        print(f"Flights with a real (non-normal) label : {int(has_real_fault.sum())}")
        print(f"  -> anomaly model flagged {flagged_among_faulty:.1%} of these as anomalous")
        print(f"Flights labelled normal/unlabelled      : {int((~has_real_fault).sum())}")
        print(f"  -> anomaly model flagged {flagged_among_normal:.1%} of these as anomalous")
        print(
            "\n[i] Ideally the first percentage is noticeably higher than the second - that "
            "would suggest the anomaly signal correlates with real faults, even though it was "
            "trained without using the labels. This is diagnostic context for your SIH report, "
            "not a substitute for the fault classifier's supervised metrics above."
        )
    else:
        print("Anomaly model or 'label' column not available for this cross-check.")


if __name__ == "__main__":
    main()
