"""
ml/train_fault_model.py
=========================
STEP (after ml/create_features.py; can run before or after
ml/train_anomaly_model.py).

Trains a supervised classifier to predict the fault label
(flight_header.csv's `label` column by default - exactly the strings
NGAFID provides, e.g. "intake gasket leak/damage"). We NEVER invent
new fault names; the model can only output labels it saw in training.

LABELLING DECISION (documented): flights with a missing/NaN label are
treated as an explicit "normal" class, not dropped. Without this, the
classifier would only ever have seen fault examples and would be
biased to always predict SOME fault - which would make every replayed
flight in the demo look broken. "normal" is also the exact keyword
app/services/fault_prediction_service.py checks for to decide
fault_detected=False.

RARE CLASSES: fault types with fewer than --min-class-count examples
are grouped into a single "other_rare_fault" class so train/test
splitting and evaluation are statistically meaningful. This is
reported clearly in the output and in models/metrics.json.

MODEL: RandomForestClassifier by default (simple, no extra native
dependencies, robust to unscaled/odd features). If you run with
--model xgboost AND have xgboost installed, it will use that instead.

USAGE:

    python ml/train_fault_model.py
    python ml/train_fault_model.py --target target_class
    python ml/train_fault_model.py --model xgboost
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler

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


def prepare_X(df: pd.DataFrame):
    candidate_columns = [c for c in df.columns if c not in NON_FEATURE_COLUMNS]
    fully_empty = [c for c in candidate_columns if df[c].isna().all()]
    feature_columns = [c for c in candidate_columns if c not in fully_empty]

    X_df = df[feature_columns].copy()
    for c in feature_columns:
        if X_df[c].isna().any():
            X_df[c] = X_df[c].fillna(X_df[c].median())

    return X_df.values.astype(np.float64), feature_columns, fully_empty


def prepare_y(df: pd.DataFrame, target: str, min_class_count: int):
    if target not in df.columns:
        print(f"[error] target column '{target}' not found in flight_features.csv. "
              f"Available: {list(df.columns)}")
        sys.exit(1)

    y = df[target].fillna("normal").astype(str)
    counts = y.value_counts()
    rare_classes = counts[counts < min_class_count].index.tolist()
    if rare_classes:
        print(f"Grouping {len(rare_classes)} rare classes (< {min_class_count} examples) "
              f"into 'other_rare_fault': {rare_classes}")
        y = y.replace(rare_classes, "other_rare_fault")

    return y


def build_model(model_name: str, n_estimators: int):
    if model_name == "xgboost":
        try:
            from xgboost import XGBClassifier  # noqa: F401
        except ImportError:
            print("[warn] xgboost not installed - falling back to RandomForestClassifier. "
                  "Install with: pip install xgboost")
        else:
            from xgboost import XGBClassifier
            print(f"Using XGBClassifier(n_estimators={n_estimators})")
            return XGBClassifier(
                n_estimators=n_estimators, max_depth=6, random_state=42,
                eval_metric="mlogloss", n_jobs=-1,
            )

    print(f"Using RandomForestClassifier(n_estimators={n_estimators})")
    return RandomForestClassifier(
        n_estimators=n_estimators, max_depth=None, class_weight="balanced",
        random_state=42, n_jobs=-1,
    )


def main():
    parser = argparse.ArgumentParser(description="Train the fault classification model.")
    parser.add_argument("--target", type=str, default="label", help="Which header column to predict (default: label)")
    parser.add_argument("--min-class-count", type=int, default=5, help="Classes with fewer examples are grouped into 'other_rare_fault'")
    parser.add_argument("--model", choices=["random_forest", "xgboost"], default="random_forest")
    parser.add_argument("--n-estimators", type=int, default=300)
    parser.add_argument("--test-size", type=float, default=0.2)
    args = parser.parse_args()

    df = load_features()
    print(f"Loaded feature table: {df.shape}")

    X, feature_columns, fully_empty = prepare_X(df)
    print(f"Dropping {len(fully_empty)} fully-empty feature columns (unmapped sensors): {fully_empty}")
    print(f"Training on {len(feature_columns)} feature columns.")

    y = prepare_y(df, args.target, args.min_class_count)
    print(f"\nClass distribution (target='{args.target}'):")
    print(y.value_counts().to_string())

    encoder = LabelEncoder()
    y_encoded = encoder.fit_transform(y)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y_encoded, test_size=args.test_size, random_state=42, stratify=y_encoded
        )
    except ValueError as exc:
        print(f"[warn] Stratified split failed ({exc}); falling back to a plain random split. "
              f"Consider raising --min-class-count.")
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y_encoded, test_size=args.test_size, random_state=42
        )

    model = build_model(args.model, args.n_estimators)
    print(f"\nTraining on {len(X_train)} flights, testing on {len(X_test)} flights...")
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    accuracy = float(accuracy_score(y_test, y_pred))
    macro_f1 = float(f1_score(y_test, y_pred, average="macro"))
    report = classification_report(
        y_test, y_pred, target_names=encoder.classes_, output_dict=True, zero_division=0
    )

    print(f"\nTest accuracy: {accuracy:.3f}")
    print(f"Test macro F1: {macro_f1:.3f}")
    print("\nClassification report:")
    print(classification_report(y_test, y_pred, target_names=encoder.classes_, zero_division=0))

    settings.MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, settings.FAULT_MODEL_PATH)
    joblib.dump(scaler, settings.SCALER_PATH)
    joblib.dump(encoder, settings.LABEL_ENCODER_PATH)
    with open(settings.FEATURE_COLUMNS_PATH, "w", encoding="utf-8") as f:
        json.dump(feature_columns, f, indent=2)

    metrics = {}
    if settings.METRICS_PATH.exists():
        with open(settings.METRICS_PATH, "r", encoding="utf-8") as f:
            metrics = json.load(f)
    metrics["fault_model"] = {
        "target_column": args.target,
        "model": args.model,
        "n_estimators": args.n_estimators,
        "classes": list(encoder.classes_),
        "train_flights": len(X_train),
        "test_flights": len(X_test),
        "test_accuracy": accuracy,
        "test_macro_f1": macro_f1,
        "classification_report": report,
        "note": "Metrics are on a held-out test split of the available labelled NGAFID data. "
                "Rare classes below --min-class-count were grouped into 'other_rare_fault'.",
    }
    with open(settings.METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print(f"\nSaved:\n  {settings.FAULT_MODEL_PATH}\n  {settings.SCALER_PATH}\n"
          f"  {settings.LABEL_ENCODER_PATH}\n  {settings.FEATURE_COLUMNS_PATH}")
    print(f"Metrics merged into: {settings.METRICS_PATH}")
    print("\nNext step: python ml/evaluate_models.py")


if __name__ == "__main__":
    main()
