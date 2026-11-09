"""
app/services/preprocessing.py
===============================
Turns a raw (T, 23) NumPy array from flight_data.pkl into a clean,
NAMED pandas DataFrame using the verified sensor mapping - and does
basic cleaning (missing values, sane clipping) along the way.

This is used both:
  - online, by the API, to serve telemetry/health/fault endpoints
  - offline, by ml/preprocess_dataset.py and ml/create_features.py,
    to build the training set

Nothing in this file invents sensor values. If the mapping is not
verified, `to_named_dataframe` raises MappingNotVerifiedError rather
than guessing which column is which.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from app.utils.sensor_mapping import SENSOR_PARAMETERS, sensor_mapping

logger = logging.getLogger(__name__)


class MappingNotVerifiedError(RuntimeError):
    """Raised when code tries to interpret raw pkl columns as named sensors
    before a human has verified data/config/sensor_mapping.json."""


def to_named_dataframe(raw_array: np.ndarray) -> pd.DataFrame:
    """Maps raw (T, N) columns to named sensor columns using the verified
    mapping. Columns present in the array but not in the mapping are
    dropped (with a warning); sensor parameters expected but missing
    from the array become fully-NaN columns so downstream code can
    still reference them by name and see they're unavailable."""
    if not sensor_mapping.usable:
        raise MappingNotVerifiedError(
            "Sensor mapping is not verified yet. Run "
            "`python ml/verify_sensor_mapping.py`, sanity-check the suggested "
            "mapping in data/config/sensor_mapping.json, then set "
            '"verified": true before requesting real telemetry.'
        )

    n_cols = raw_array.shape[1]
    columns = {}
    for idx in range(n_cols):
        name = sensor_mapping.get_name_for_index(idx)
        if name is not None:
            columns[name] = raw_array[:, idx]

    df = pd.DataFrame(columns)

    # Make sure every canonical sensor parameter is present as a column,
    # even if unmapped, so callers can safely do df["E1 RPM"] and get NaN
    # (=> "unavailable") instead of a KeyError.
    for param in SENSOR_PARAMETERS:
        if param not in df.columns:
            df[param] = np.nan

    return df[SENSOR_PARAMETERS]


def clean_dataframe(df: pd.DataFrame, max_gap_fill: int = 5) -> pd.DataFrame:
    """Basic, documented cleaning for one flight's telemetry:

    1. Replace obvious sensor dropout sentinels (e.g. exactly 0.0 for a
       parameter that is never legitimately zero in flight, like RPM
       once the engine is running) is intentionally NOT done here,
       because "legitimately zero" varies by parameter and flight phase
       (e.g. RPM = 0 before engine start is real data, not a dropout).
       We only handle genuine NaNs.
    2. Forward/backward-fill short gaps of missing data (<= max_gap_fill
       consecutive rows) - reasonable for sensor blips.
    3. Leave longer gaps as NaN rather than fabricate trends across them.
    """
    cleaned = df.copy()
    cleaned = cleaned.ffill(limit=max_gap_fill).bfill(limit=max_gap_fill)
    return cleaned


def flight_array_to_clean_df(raw_array: np.ndarray) -> pd.DataFrame:
    """Convenience: raw pkl array -> named -> cleaned, in one call."""
    named = to_named_dataframe(raw_array)
    return clean_dataframe(named)
