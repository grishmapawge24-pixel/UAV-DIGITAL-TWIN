"""
ml/save_models.py
===================
STEP (last one - run this right before your demo).

Doesn't train anything new. Just verifies every expected model
artifact is present in backend/models/, prints a short "model card"
summary (sizes, when trained, key metrics from models/metrics.json),
and gives a clear PASS/FAIL checklist so you know the backend is ready
to serve real predictions before you start the FastAPI server.

USAGE:

    python ml/save_models.py
"""

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings

EXPECTED = [
    ("Anomaly model", settings.ANOMALY_MODEL_PATH),
    ("Fault model", settings.FAULT_MODEL_PATH),
    ("Scaler", settings.SCALER_PATH),
    ("Label encoder", settings.LABEL_ENCODER_PATH),
    ("Feature columns", settings.FEATURE_COLUMNS_PATH),
]


def human_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def main():
    print("=" * 78)
    print("MODEL ARTIFACT CHECK")
    print("=" * 78)

    all_ok = True
    for label, path in EXPECTED:
        exists = path.exists()
        all_ok = all_ok and exists
        if exists:
            stat = path.stat()
            when = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
            print(f"[OK]   {label:<18} {human_size(stat.st_size):>10}   modified {when}   {path}")
        else:
            print(f"[MISSING] {label:<18} {path}")

    print()
    if settings.METRICS_PATH.exists():
        with open(settings.METRICS_PATH, "r", encoding="utf-8") as f:
            metrics = json.load(f)
        fm = metrics.get("fault_model")
        if fm:
            print(f"Fault model: {fm['model']}, test accuracy {fm['test_accuracy']:.3f}, "
                  f"macro F1 {fm['test_macro_f1']:.3f}, {len(fm['classes'])} classes")
        am = metrics.get("anomaly_model")
        if am:
            print(f"Anomaly model: {am['n_estimators']} trees, "
                  f"{am['training_anomaly_fraction']:.1%} of training flights flagged anomalous")
    else:
        print("[warn] No models/metrics.json found yet.")

    print("\n" + "=" * 78)
    if all_ok:
        print("ALL MODEL ARTIFACTS PRESENT - the API's /api/health endpoint should report "
              "anomaly_model_loaded=true and fault_model_loaded=true.")
        print("Start the backend with: uvicorn app.main:app --reload")
    else:
        print("SOME ARTIFACTS ARE MISSING. Run, in order:")
        print("  python ml/verify_sensor_mapping.py   (then set \"verified\": true in the json)")
        print("  python ml/create_features.py")
        print("  python ml/train_anomaly_model.py")
        print("  python ml/train_fault_model.py")
    print("=" * 78)


if __name__ == "__main__":
    main()
