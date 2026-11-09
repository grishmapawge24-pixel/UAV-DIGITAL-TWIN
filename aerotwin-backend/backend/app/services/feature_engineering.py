"""
app/services/feature_engineering.py
=====================================
Converts one flight's cleaned, named telemetry DataFrame (see
preprocessing.py) into a single flat feature vector (a dict of
scalar values) suitable for the anomaly and fault-classification
models.

IMPORTANT: this exact function is used both offline, when building the
training set (ml/create_features.py), and online, at inference time
(anomaly_service.py, fault_prediction_service.py). Using the same code
in both places is what guarantees "the features the model sees at
inference match what it was trained on" - a very common source of bugs
if you compute features differently in two places.

Feature families per sensor channel (as requested in the brief):
    mean, std, min, max, median, range, slope,
    rolling_mean_std (mean of a rolling std, i.e. "how noisy is this
        channel, on average, in short windows" - a simple vibration-ish
        proxy computed from the channels we DO have; NOT a substitute
        for a real vibration sensor, and never presented as one),
    rate_of_change (mean absolute first difference)

We do NOT fabricate values for parameters the mapping says are
unavailable (all-NaN columns) - their features are simply NaN, and the
training script drops/imputes them consistently with the deployed
scaler so the API does the same at inference time.
"""

from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd

from app.services.data_service import data_service
from app.services.preprocessing import flight_array_to_clean_df
from app.utils.sensor_mapping import SENSOR_PARAMETERS

# Engine "health" channels the brief specifically calls out for feature
# engineering. Environment channels are included too, but with a lighter
# feature set (they describe conditions, not engine wear).
HEALTH_CHANNELS = [
    "E1 RPM", "E1 CHT1", "E1 CHT2", "E1 CHT3", "E1 CHT4",
    "E1 EGT1", "E1 EGT2", "E1 EGT3", "E1 EGT4",
    "E1 OilP", "E1 OilT", "E1 FFlow",
    "volt1", "volt2", "amp1", "amp2", "FQtyL", "FQtyR",
]
ENVIRONMENT_CHANNELS = ["OAT", "IAS", "VSpd", "AltMSL"]

ROLLING_WINDOW = 20  # timesteps; ~ a few seconds depending on sample rate


def _safe_slope(y: np.ndarray) -> float:
    """Linear regression slope of y against its own index. NaN-safe."""
    valid = ~np.isnan(y)
    if valid.sum() < 2:
        return np.nan
    x = np.arange(len(y))[valid]
    y_valid = y[valid]
    # Guard against a degenerate all-identical-x case (can't happen here,
    # x is always 0..n-1, but keeps this function safe for reuse).
    if np.all(x == x[0]):
        return 0.0
    slope, _intercept = np.polyfit(x, y_valid, 1)
    return float(slope)


def _channel_features(series: pd.Series, prefix: str, full: bool = True) -> Dict[str, float]:
    values = series.to_numpy(dtype=np.float64)
    feats: Dict[str, float] = {}

    if np.all(np.isnan(values)):
        # Whole channel unavailable (unmapped parameter) - be explicit
        # with NaN rather than silently defaulting to 0, which would look
        # like a real (and alarming!) sensor reading of zero.
        keys = ["mean", "std", "min", "max", "median", "range"]
        if full:
            keys += ["slope", "rolling_std_mean", "rate_of_change"]
        for k in keys:
            feats[f"{prefix}_{k}"] = np.nan
        return feats

    feats[f"{prefix}_mean"] = float(np.nanmean(values))
    feats[f"{prefix}_std"] = float(np.nanstd(values))
    feats[f"{prefix}_min"] = float(np.nanmin(values))
    feats[f"{prefix}_max"] = float(np.nanmax(values))
    feats[f"{prefix}_median"] = float(np.nanmedian(values))
    feats[f"{prefix}_range"] = feats[f"{prefix}_max"] - feats[f"{prefix}_min"]

    if full:
        feats[f"{prefix}_slope"] = _safe_slope(values)

        s = pd.Series(values)
        rolling_std = s.rolling(window=ROLLING_WINDOW, min_periods=max(2, ROLLING_WINDOW // 4)).std()
        feats[f"{prefix}_rolling_std_mean"] = (
            float(np.nanmean(rolling_std)) if not rolling_std.isna().all() else np.nan
        )

        diffs = np.diff(values[~np.isnan(values)])
        feats[f"{prefix}_rate_of_change"] = float(np.nanmean(np.abs(diffs))) if len(diffs) else np.nan

    return feats


def clean_key(param: str) -> str:
    return param.replace(" ", "_")


def compute_flight_features(df: pd.DataFrame) -> Dict[str, float]:
    """df must already be a named, cleaned DataFrame (see preprocessing.py),
    with one column per SENSOR_PARAMETERS entry (NaN columns allowed for
    unavailable sensors)."""
    features: Dict[str, float] = {}

    for channel in HEALTH_CHANNELS:
        if channel not in df.columns:
            continue
        features.update(_channel_features(df[channel], clean_key(channel), full=True))

    for channel in ENVIRONMENT_CHANNELS:
        if channel not in df.columns:
            continue
        features.update(_channel_features(df[channel], clean_key(channel), full=False))

    features["flight_num_timesteps"] = float(len(df))

    return features


def get_features_for_flight(flight_id: int) -> Dict[str, float]:
    """One-stop helper: raw pkl array -> named/cleaned DataFrame -> feature
    vector, for a single flight_id. Used by both the offline training
    script (ml/create_features.py) and the online inference services
    (anomaly_service.py, fault_prediction_service.py, health_index_service.py)
    so features are always computed identically."""
    raw = data_service.get_flight_array(flight_id)
    df = flight_array_to_clean_df(raw)
    return compute_flight_features(df)


def feature_names() -> List[str]:
    """The full, deterministic list of feature names this module can produce,
    useful for building a training DataFrame with consistent columns even
    when some flights are missing some channels."""
    dummy_len = 30
    dummy = pd.DataFrame(
        {p: np.linspace(0, 1, dummy_len) for p in SENSOR_PARAMETERS}
    )
    return sorted(compute_flight_features(dummy).keys())
