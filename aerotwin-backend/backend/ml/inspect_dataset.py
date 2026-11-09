"""
ml/inspect_dataset.py
=======================
STEP 1 of the ML pipeline.

Run this FIRST, before anything else. It just looks at your NGAFID
files and prints what's actually in them - no mapping assumptions, no
training, nothing is written to disk. Goal: build confidence that
NGAFID_DATA_PATH is set correctly and the files match what the project
brief described, before you spend time on later steps.

USAGE (from the backend/ folder, virtual env activated):

    python ml/inspect_dataset.py
    python ml/inspect_dataset.py --full-scan          # also loads flight_data.pkl (slow, ~2.7GB)
    python ml/inspect_dataset.py --full-scan --sample 300   # scan 300 flights instead of the default 100
"""

import argparse
import os
import pickle
import sys
import time
from pathlib import Path

# Make `import app...` work no matter where this script is invoked from.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd

from app.config import settings


def human_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"


def section(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def inspect_paths() -> bool:
    section("0. PATHS")
    print(f"NGAFID_DATA_PATH        = {settings.NGAFID_DATA_PATH!r}")
    ok = True
    for label, path in (
        ("flight_header.csv", settings.flight_header_path),
        ("flight_data.pkl", settings.flight_data_pkl_path),
        ("stats.csv", settings.stats_csv_path),
    ):
        exists = path.exists()
        size = human_size(path.stat().st_size) if exists else "-"
        print(f"  {label:<20} {'FOUND' if exists else 'MISSING':<8} {size:>12}   {path}")
        ok = ok and exists
    if not ok:
        print(
            "\n[!] At least one file is missing. Check NGAFID_DATA_PATH in backend/.env "
            "and the filenames above (FLIGHT_HEADER_FILENAME / FLIGHT_DATA_FILENAME / "
            "STATS_FILENAME env vars if your files are named differently)."
        )
    return ok


def inspect_header() -> pd.DataFrame:
    section("1. flight_header.csv")
    df = pd.read_csv(settings.flight_header_path)
    print(f"shape: {df.shape}")
    print(f"columns: {list(df.columns)}")
    print("\ndtypes:")
    print(df.dtypes)
    print("\nhead:")
    print(df.head(5).to_string())
    print("\nmissing values per column:")
    print(df.isna().sum())

    for col in ("label", "target_class", "hclass", "before_after", "class"):
        if col in df.columns:
            print(f"\nvalue_counts('{col}') [top 20]:")
            print(df[col].value_counts(dropna=False).head(20).to_string())

    for col in ("flight_length", "date_diff", "number_flights_before"):
        if col in df.columns:
            print(f"\ndescribe('{col}'):")
            print(df[col].describe().to_string())

    return df


def inspect_stats() -> pd.DataFrame:
    section("2. stats.csv")
    df = pd.read_csv(settings.stats_csv_path)
    print(f"shape: {df.shape}")
    print(f"columns: {list(df.columns)}")
    print("\nfull contents (stats.csv is expected to be small):")
    with pd.option_context("display.max_rows", 200, "display.max_columns", 50, "display.width", 160):
        print(df.to_string())
    print(
        "\n[i] Take note of whether stats.csv has ONE ROW PER PARAMETER (e.g. columns like "
        "name/mean/std/min/max) - if so, ml/verify_sensor_mapping.py can use row order and/or "
        "these statistics to match stats.csv parameters to flight_data.pkl's 23 numeric columns."
    )
    return df


def inspect_pkl_light() -> None:
    section("3. flight_data.pkl (light check - file size only)")
    size = settings.flight_data_pkl_path.stat().st_size
    print(f"file size: {human_size(size)}")
    print(
        "Not loading it (use --full-scan to actually open it - this will use a lot of RAM "
        "and can take a couple of minutes for a ~2.7GB file)."
    )


def inspect_pkl_full(sample: int) -> None:
    section("3. flight_data.pkl (full scan)")
    print("Loading the full pickle file into memory - this is the slow part, please wait...")
    t0 = time.time()
    with open(settings.flight_data_pkl_path, "rb") as f:
        data = pickle.load(f)
    print(f"Loaded in {time.time() - t0:.1f}s. Total flights in dict: {len(data)}")

    flight_ids = list(data.keys())
    print(f"flight_id dtype/example keys: {[type(k).__name__ for k in flight_ids[:3]]} {flight_ids[:5]}")

    shapes = set()
    dtypes = set()
    sample_ids = flight_ids[: min(sample, len(flight_ids))]
    print(f"\nInspecting a sample of {len(sample_ids)} flights...")
    n_cols_seen = set()
    all_lengths = []
    for fid in sample_ids:
        arr = data[fid]
        shapes.add(arr.shape[1] if arr.ndim == 2 else None)
        dtypes.add(str(arr.dtype))
        n_cols_seen.add(arr.shape[1] if arr.ndim == 2 else None)
        all_lengths.append(arr.shape[0])

    print(f"array dtypes seen: {dtypes}")
    print(f"array column-counts seen: {n_cols_seen} (brief says 23)")
    print(f"flight length (timesteps) - min/mean/max over sample: "
          f"{min(all_lengths)} / {np.mean(all_lengths):.1f} / {max(all_lengths)}")

    first_id = sample_ids[0]
    print(f"\nExample: flight_data[{first_id}].shape = {data[first_id].shape}, dtype = {data[first_id].dtype}")
    print(f"First 3 rows of flight {first_id} (raw, unmapped columns):")
    with np.printoptions(precision=3, suppress=True, linewidth=160):
        print(data[first_id][:3])

    # Per-column-index basic stats over the sample - this is exactly the
    # kind of information ml/verify_sensor_mapping.py compares against
    # stats.csv to suggest a mapping.
    n_cols = data[first_id].shape[1]
    print(f"\nPer-column-index stats over {len(sample_ids)} sampled flights (mean of per-flight mean/min/max):")
    col_means, col_mins, col_maxs = [], [], []
    for c in range(n_cols):
        vals = []
        for fid in sample_ids:
            arr = data[fid]
            if arr.shape[1] == n_cols:
                vals.append(arr[:, c].astype(np.float32))
        allv = np.concatenate(vals) if vals else np.array([])
        allv = allv[~np.isnan(allv)]
        if len(allv) == 0:
            col_means.append(np.nan); col_mins.append(np.nan); col_maxs.append(np.nan)
            continue
        col_means.append(float(np.mean(allv)))
        col_mins.append(float(np.min(allv)))
        col_maxs.append(float(np.max(allv)))

    stats_preview = pd.DataFrame(
        {"column_index": range(n_cols), "mean": col_means, "min": col_mins, "max": col_maxs}
    )
    print(stats_preview.to_string(index=False))
    print(
        "\n[i] Compare these ranges by eye against stats.csv's parameter names (e.g. a column "
        "with mean ~2500-4500 and max ~5000+ is very likely E1 RPM; a column with values "
        "roughly 12-30 is very likely volt1/volt2, etc). ml/verify_sensor_mapping.py automates "
        "this comparison and writes a candidate mapping for you to confirm."
    )


def main():
    parser = argparse.ArgumentParser(description="Inspect the raw NGAFID dataset files.")
    parser.add_argument("--full-scan", action="store_true", help="Also load and inspect flight_data.pkl")
    parser.add_argument("--sample", type=int, default=100, help="Number of flights to sample for --full-scan")
    args = parser.parse_args()

    if not inspect_paths():
        sys.exit(1)

    inspect_header()
    inspect_stats()

    if args.full_scan:
        inspect_pkl_full(args.sample)
    else:
        inspect_pkl_light()

    section("DONE")
    print("Next step: python ml/verify_sensor_mapping.py")


if __name__ == "__main__":
    main()
