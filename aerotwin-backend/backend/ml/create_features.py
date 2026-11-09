"""
ml/create_features.py
=======================
STEP (after ml/verify_sensor_mapping.py is verified=true).

Builds the full training feature table: one row per flight, with the
same engineered features `app.services.feature_engineering` computes
online for the API (mean/std/min/max/median/range/slope/rolling-std/
rate-of-change per sensor channel), plus the label columns from
flight_header.csv needed for training.

Output: backend/data/features/flight_features.csv

USAGE:

    python ml/create_features.py
    python ml/create_features.py --limit 500      # quick test run on a subset
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd

from app.config import settings
from app.services.data_service import data_service
from app.services.feature_engineering import compute_flight_features, feature_names
from app.services.preprocessing import MappingNotVerifiedError, flight_array_to_clean_df
from app.utils.sensor_mapping import sensor_mapping

LABEL_COLUMNS = [
    "label", "before_after", "date_diff", "flight_length", "hierarchy",
    "fold", "class", "target_class", "hclass", "number_flights_before",
]


def main():
    parser = argparse.ArgumentParser(description="Build the training feature table from NGAFID flights.")
    parser.add_argument("--limit", type=int, default=None, help="Only process the first N flights (for a quick test run)")
    args = parser.parse_args()

    if not settings.dataset_configured():
        print("[error] NGAFID_DATA_PATH is not configured. Set it in backend/.env first.")
        sys.exit(1)

    if not sensor_mapping.usable:
        print(
            "[error] Sensor mapping is not verified yet. Run ml/verify_sensor_mapping.py, "
            "check data/config/sensor_mapping.json, and set \"verified\": true before "
            "building features - otherwise the columns would be meaningless."
        )
        sys.exit(1)

    header = data_service.load_header()
    flight_ids = header.index.tolist()
    if args.limit:
        flight_ids = flight_ids[: args.limit]

    columns = feature_names()
    print(f"Building {len(columns)} engineered features for {len(flight_ids)} flights...")

    rows = []
    ok, failed = 0, 0
    t0 = time.time()
    for i, fid in enumerate(flight_ids, start=1):
        try:
            raw = data_service.get_flight_array(int(fid))
            df = flight_array_to_clean_df(raw)
            feats = compute_flight_features(df)
        except (KeyError, FileNotFoundError, MappingNotVerifiedError) as exc:
            failed += 1
            continue

        row = {"flight_id": int(fid)}
        for col in columns:
            row[col] = feats.get(col, np.nan)
        for col in LABEL_COLUMNS:
            if col in header.columns:
                row[col] = header.loc[fid, col]
        rows.append(row)
        ok += 1

        if i % 500 == 0:
            elapsed = time.time() - t0
            print(f"  ...{i}/{len(flight_ids)} ({elapsed:.0f}s elapsed, {ok} ok / {failed} failed)")

    features_df = pd.DataFrame(rows)
    settings.FEATURES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = settings.FEATURES_DIR / "flight_features.csv"
    features_df.to_csv(out_path, index=False)

    print(f"\nDone in {time.time() - t0:.0f}s. ok={ok} failed={failed}")
    print(f"Feature table shape: {features_df.shape}")
    print(f"Saved to: {out_path}")

    if "label" in features_df.columns:
        print("\nLabel distribution (top 15):")
        print(features_df["label"].value_counts(dropna=False).head(15).to_string())

    print("\nNext step: python ml/train_anomaly_model.py")
    print("           python ml/train_fault_model.py")


if __name__ == "__main__":
    main()
