"""
ml/verify_sensor_mapping.py
=============================
STEP 2 of the ML pipeline. THE MOST IMPORTANT SCRIPT IN THIS PROJECT.

flight_data.pkl gives each flight as a (T, 23) array of UNNAMED numeric
columns. stats.csv gives NAMED parameters. Nothing in the raw dataset
directly says "pkl column 7 = E1 OilP". This script does NOT assume a
mapping - it statistically SUGGESTS one, prints it for you to visually
sanity-check, and writes it to data/config/sensor_mapping.json with
"verified": false. Nothing downstream (features, training, the API)
will treat the mapping as trustworthy until you open that file and
change it to "verified": true yourself.

HOW IT WORKS
-------------
1. Reads stats.csv and tries to figure out its structure automatically
   (long format: one row per parameter with mean/std/min/max columns,
   OR wide format: one column per parameter). Either way, it ends up
   with per-parameter summary statistics (mean/std/min/max) computed
   FROM stats.csv.
2. Samples a configurable number of real flights from flight_data.pkl
   (via the processed cache if you've already run
   ml/preprocess_dataset.py - much faster) and computes the SAME
   summary statistics per raw column index.
3. Solves an optimal one-to-one assignment (Hungarian algorithm, via
   scipy) between pkl columns and stats.csv parameters, minimising a
   scale-normalised distance between their statistics.
4. Prints the suggested mapping with a confidence score AND typical
   general-aviation value ranges (hard-coded domain knowledge, for your
   own sanity check only - NOT used by the matching algorithm) so you
   can eyeball whether "column 9 -> E1 RPM, confidence 0.94, typical
   range 500-2700" actually looks right.
5. Writes data/config/sensor_mapping.json with verified=false.

USAGE:

    python ml/verify_sensor_mapping.py
    python ml/verify_sensor_mapping.py --sample 300

THEN: open backend/data/config/sensor_mapping.json, check the mapping
against the printed table (and your own knowledge of the aircraft/
engine instrumentation if you have it), fix anything wrong, and change
"verified": false to "verified": true. Only then run the rest of the
pipeline.
"""

import argparse
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment

from app.config import settings
from app.services.data_service import data_service
from app.utils.sensor_mapping import ALL_STATS_PARAMETERS, SENSOR_PARAMETERS

# Purely informational - printed next to each suggestion so a human can
# sanity-check it. NOT used anywhere in the matching math. Broad ranges for
# a small piston aircraft engine / light airframe; your specific
# airframe/engine may differ.
TYPICAL_RANGES = {
    "volt1": "~12-30 V", "volt2": "~12-30 V",
    "amp1": "~-60 to 60 A", "amp2": "~-60 to 60 A",
    "FQtyL": "~0-50 gal", "FQtyR": "~0-50 gal",
    "E1 FFlow": "~0-20 gph",
    "E1 OilT": "~100-220 \u00b0F", "E1 OilP": "~30-90 psi",
    "E1 RPM": "~500-2700 RPM",
    "E1 CHT1": "~200-400 \u00b0F", "E1 CHT2": "~200-400 \u00b0F",
    "E1 CHT3": "~200-400 \u00b0F", "E1 CHT4": "~200-400 \u00b0F",
    "E1 EGT1": "~1200-1600 \u00b0F", "E1 EGT2": "~1200-1600 \u00b0F",
    "E1 EGT3": "~1200-1600 \u00b0F", "E1 EGT4": "~1200-1600 \u00b0F",
    "OAT": "~-20 to 40 \u00b0C", "IAS": "~0-200 kt",
    "VSpd": "~-2000 to 2000 fpm", "NormAc": "~-2 to 4 g",
    "AltMSL": "~0-15000 ft",
    "timestep": "monotonic index/time", "cluster": "small integer cluster id",
}

STAT_KEYS = ["mean", "std", "min", "max"]


def find_name_column(df: pd.DataFrame) -> str:
    """Long-format guess: which column's *values* look like our known
    parameter names?"""
    best_col, best_overlap = None, 0
    known = set(ALL_STATS_PARAMETERS)
    for col in df.columns:
        try:
            overlap = df[col].astype(str).isin(known).sum()
        except Exception:  # noqa: BLE001
            continue
        if overlap > best_overlap:
            best_overlap, best_col = overlap, col
    return best_col if best_overlap >= max(3, len(known) // 4) else None


def find_stat_columns(df: pd.DataFrame) -> dict:
    """Long-format guess: which numeric columns look like mean/std/min/max?"""
    found = {}
    for key in STAT_KEYS:
        for col in df.columns:
            if key == col.strip().lower() or key in col.strip().lower():
                if pd.api.types.is_numeric_dtype(df[col]):
                    found[key] = col
                    break
    return found


def stats_from_long_format(df: pd.DataFrame, name_col: str) -> dict:
    stat_cols = find_stat_columns(df)
    result = {}
    for _, row in df.iterrows():
        name = str(row[name_col])
        entry = {}
        for key, col in stat_cols.items():
            try:
                entry[key] = float(row[col])
            except (TypeError, ValueError):
                entry[key] = np.nan
        result[name] = entry
    return result, stat_cols


def stats_from_wide_format(df: pd.DataFrame) -> dict:
    """Wide-format guess: columns ARE parameter names; compute mean/std/
    min/max down each column, treating every row as a sample/record."""
    # NGAFID's compact stats.csv has one row of means followed by one row of
    # standard deviations (rather than one observation per row).  Treating
    # those two summary values as raw samples corrupts the matching score.
    # Detect that shape and preserve the supplied statistics directly.
    if len(df) == 2:
        result = {}
        for col in df.columns:
            if col not in ALL_STATS_PARAMETERS:
                continue
            values = pd.to_numeric(df[col], errors="coerce")
            if values.notna().sum() == 2:
                result[col] = {
                    "mean": float(values.iloc[0]),
                    "std": float(abs(values.iloc[1])),
                }
        if result:
            print("[detect] stats.csv contains compact mean/std summary rows.")
            return result

    result = {}
    for col in df.columns:
        if col not in ALL_STATS_PARAMETERS:
            continue
        series = pd.to_numeric(df[col], errors="coerce")
        if series.notna().sum() == 0:
            continue
        result[col] = {
            "mean": float(series.mean()),
            "std": float(series.std()),
            "min": float(series.min()),
            "max": float(series.max()),
        }
    return result


def load_stats_csv_statistics() -> dict:
    df = pd.read_csv(settings.stats_csv_path)
    name_col = find_name_column(df)

    if name_col is not None:
        print(f"[detect] stats.csv looks LONG-format: parameter name column = '{name_col}'")
        stats_dict, stat_cols = stats_from_long_format(df, name_col)
        print(f"[detect] matched statistic columns: {stat_cols}")
        return stats_dict

    wide_stats = stats_from_wide_format(df)
    if wide_stats:
        print(
            f"[detect] stats.csv looks WIDE-format: {len(wide_stats)} of its columns match "
            "known parameter names; computing mean/std/min/max down each column."
        )
        return wide_stats

    print(
        "[warn] Could not automatically detect stats.csv's structure "
        "(no parameter-name column found, and column headers don't match known "
        "parameter names). Printing a raw preview - you may need to adapt "
        "load_stats_csv_statistics() in this script to your file's actual layout."
    )
    print(df.head(10).to_string())
    return {}


def compute_pkl_column_statistics(sample_size: int) -> dict:
    header = data_service.load_header()
    all_ids = header.index.tolist()
    random.seed(42)  # reproducible sample
    sample_ids = random.sample(all_ids, min(sample_size, len(all_ids)))

    print(f"[scan] Sampling {len(sample_ids)} of {len(all_ids)} flights from flight_data.pkl "
          f"(uses the processed cache automatically if you've run ml/preprocess_dataset.py)...")

    per_col_values = None
    n_cols = None
    used = 0
    for fid in sample_ids:
        try:
            arr = data_service.get_flight_array(int(fid))
        except (KeyError, FileNotFoundError):
            continue
        if n_cols is None:
            n_cols = arr.shape[1]
            per_col_values = [[] for _ in range(n_cols)]
        if arr.shape[1] != n_cols:
            continue
        for c in range(n_cols):
            col = arr[:, c]
            col = col[~np.isnan(col)]
            if len(col):
                per_col_values[c].append(col)
        used += 1

    print(f"[scan] Successfully read {used}/{len(sample_ids)} sampled flights. Raw array has {n_cols} columns.")

    col_stats = {}
    for c in range(n_cols):
        if per_col_values[c]:
            allv = np.concatenate(per_col_values[c])
            col_stats[c] = {
                "mean": float(np.mean(allv)),
                "std": float(np.std(allv)),
                "min": float(np.min(allv)),
                "max": float(np.max(allv)),
            }
        else:
            col_stats[c] = {"mean": np.nan, "std": np.nan, "min": np.nan, "max": np.nan}
    return col_stats, n_cols


def rel_distance(a: float, b: float) -> float:
    if np.isnan(a) or np.isnan(b):
        return 1.0  # neutral-ish penalty when a stat is missing on either side
    return abs(a - b) / (abs(a) + abs(b) + 1e-6)


def build_cost_matrix(col_stats: dict, param_stats: dict, n_cols: int, param_names: list) -> np.ndarray:
    cost = np.zeros((n_cols, len(param_names)))
    for i in range(n_cols):
        for j, name in enumerate(param_names):
            c = col_stats[i]
            p = param_stats[name]
            d = 0.0
            n_terms = 0
            for key in STAT_KEYS:
                if key in c and key in p:
                    d += rel_distance(c[key], p[key])
                    n_terms += 1
            cost[i, j] = (d / n_terms) if n_terms else 1.0
    return cost


def suggest_mapping(col_stats: dict, param_stats: dict, n_cols: int) -> dict:
    param_names = [p for p in param_stats.keys()]
    if not param_names:
        return {}

    cost = build_cost_matrix(col_stats, param_stats, n_cols, param_names)
    row_idx, col_idx = linear_sum_assignment(cost)

    mapping = {}
    for r, c in zip(row_idx, col_idx):
        distance = cost[r, c]
        confidence = round(max(0.0, 1.0 - distance), 3)
        mapping[r] = {
            "parameter": param_names[c],
            "confidence": confidence,
            "distance": round(float(distance), 4),
        }
    return mapping


def print_report(mapping: dict, n_cols: int) -> None:
    print("\n" + "=" * 100)
    print("SUGGESTED MAPPING (auto-generated, NOT verified - sanity check this table!)")
    print("=" * 100)
    print(f"{'pkl col':<8}{'suggested parameter':<20}{'confidence':<12}{'typical range (for your reference only)':<45}")
    print("-" * 100)
    for c in range(n_cols):
        entry = mapping.get(c)
        if not entry:
            print(f"{c:<8}{'(unmatched)':<20}{'-':<12}{'-':<45}")
            continue
        name = entry["parameter"]
        rng = TYPICAL_RANGES.get(name, "-")
        flag = "  <-- LOW CONFIDENCE, check carefully" if entry["confidence"] < 0.5 else ""
        print(f"{c:<8}{name:<20}{entry['confidence']:<12}{rng:<45}{flag}")

    matched_params = {e["parameter"] for e in mapping.values()}
    missing = [p for p in SENSOR_PARAMETERS if p not in matched_params]
    if missing:
        print(f"\nSENSOR_PARAMETERS with no suggested column at all: {missing}")


def main():
    parser = argparse.ArgumentParser(description="Suggest a pkl-column <-> parameter-name mapping for review.")
    parser.add_argument("--sample", type=int, default=200, help="Number of flights to sample for column statistics")
    args = parser.parse_args()

    if not settings.dataset_configured():
        print("[error] NGAFID_DATA_PATH is not configured. Set it in backend/.env first.")
        sys.exit(1)

    print("Step A: reading stats.csv and figuring out its structure...")
    param_stats = load_stats_csv_statistics()
    if not param_stats:
        print("[error] Could not derive per-parameter statistics from stats.csv. "
              "See the guidance printed above, adapt this script, and re-run.")
        sys.exit(1)

    print("\nStep B: computing the same statistics from flight_data.pkl columns...")
    col_stats, n_cols = compute_pkl_column_statistics(args.sample)

    print("\nStep C: solving the optimal column<->parameter assignment...")
    mapping = suggest_mapping(col_stats, param_stats, n_cols)

    print_report(mapping, n_cols)

    output = {
        "verified": False,
        "method": "Hungarian-algorithm assignment on relative distance between "
                  "stats.csv parameter statistics and sampled flight_data.pkl column statistics",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sample_size": args.sample,
        "n_raw_columns": n_cols,
        "mapping": {str(k): v for k, v in mapping.items()},
    }
    settings.SENSOR_MAPPING_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(settings.SENSOR_MAPPING_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"\nWrote suggested mapping to: {settings.SENSOR_MAPPING_PATH}")
    print(
        "\n>>> ACTION REQUIRED <<<\n"
        "Open that file, compare the suggested mapping against the printed table above "
        "(and any real documentation/telemetry-log spec you have for this aircraft's data "
        "logger, if available), correct anything wrong, then change:\n"
        '    "verified": false\n'
        "to\n"
        '    "verified": true\n'
        "Nothing else in this project will use the mapping until you do that."
    )


if __name__ == "__main__":
    main()
