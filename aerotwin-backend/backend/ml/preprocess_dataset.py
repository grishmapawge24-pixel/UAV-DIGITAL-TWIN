"""
ml/preprocess_dataset.py
==========================
STEP (performance helper - safe to run any time after inspect_dataset.py).

flight_data.pkl is one big ~2.7GB dict. Loading it fully every time you
(or the FastAPI backend) need ONE flight is slow and memory-hungry.

This script loads it ONCE and writes each flight out as its own small
.npy file under:

    backend/data/processed/flights/<flight_id>.npy

After this, `app.services.data_service.get_flight_array()` (used by the
API, and by ml/create_features.py) automatically prefers these files
and loads a single flight in milliseconds, without touching the other
~11,000 flights.

This does NOT interpret/rename columns - it's a byte-for-byte-equivalent
re-storage of the same raw (T, 23) arrays, just split up. No mapping
assumptions happen here, so it's safe to run before or after
ml/verify_sensor_mapping.py.

USAGE:

    python ml/preprocess_dataset.py
    python ml/preprocess_dataset.py --force     # re-extract even if .npy files already exist
"""

import argparse
import pickle
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd

from app.config import settings


def main():
    parser = argparse.ArgumentParser(description="Extract flight_data.pkl into per-flight .npy files.")
    parser.add_argument("--force", action="store_true", help="Re-extract even if a flight's .npy already exists")
    args = parser.parse_args()

    if not settings.dataset_configured():
        print("[error] NGAFID_DATA_PATH is not configured. Set it in backend/.env first.")
        sys.exit(1)

    out_dir = settings.PROCESSED_DIR / "flights"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading {settings.flight_data_pkl_path} (this is the slow part, ~2.7GB, please wait)...")
    t0 = time.time()
    with open(settings.flight_data_pkl_path, "rb") as f:
        data = pickle.load(f)
    print(f"Loaded {len(data)} flights in {time.time() - t0:.1f}s.")

    written, skipped, errors = 0, 0, 0
    manifest_rows = []
    t0 = time.time()
    for i, (flight_id, arr) in enumerate(data.items(), start=1):
        out_path = out_dir / f"{flight_id}.npy"
        if out_path.exists() and not args.force:
            skipped += 1
        else:
            try:
                np.save(out_path, np.asarray(arr))
                written += 1
            except Exception as exc:  # noqa: BLE001
                print(f"[warn] failed to write flight {flight_id}: {exc}")
                errors += 1
                continue

        manifest_rows.append(
            {
                "flight_id": flight_id,
                "num_timesteps": arr.shape[0] if hasattr(arr, "shape") else None,
                "num_columns": arr.shape[1] if hasattr(arr, "shape") and arr.ndim == 2 else None,
                "dtype": str(arr.dtype) if hasattr(arr, "dtype") else None,
            }
        )

        if i % 1000 == 0:
            print(f"  ...{i}/{len(data)} processed")

    manifest = pd.DataFrame(manifest_rows)
    manifest_path = settings.PROCESSED_DIR / "flight_manifest.csv"
    manifest.to_csv(manifest_path, index=False)

    print(f"\nDone in {time.time() - t0:.1f}s.")
    print(f"  written: {written}   skipped (already existed): {skipped}   errors: {errors}")
    print(f"  per-flight cache: {out_dir}")
    print(f"  manifest: {manifest_path}")
    print(
        "\nFrom now on, the API and the other ml/ scripts will load individual flights from "
        "this cache instead of the full pickle - much faster. Free to delete data/processed/ "
        "any time to reset (it will just be slower again until you re-run this script)."
    )


if __name__ == "__main__":
    main()
