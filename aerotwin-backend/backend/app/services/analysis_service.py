"""Windowed, dataset-driven analysis for historical replay.

The deployed models were trained on feature windows, not hand-entered limits.
This module applies the same feature function to a trailing window of a real
flight and compares its sensor means with the scaler baseline saved at train
time.  The small engineering knowledge layer only interprets model/deviation
signals; it never creates an anomaly by itself.
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np

from app.models.model_loader import model_bundle
from app.services import anomaly_service, fault_prediction_service, health_index_service
from app.services.data_service import data_service
from app.services.feature_engineering import clean_key, compute_flight_features
from app.services.inference_utils import get_baseline_stats
from app.services.preprocessing import flight_array_to_clean_df
from app.utils.sensor_mapping import SENSOR_PARAMETERS


def _finite(value: Any) -> bool:
    return value is not None and not (isinstance(value, float) and math.isnan(value))


def _advisories(affected: list[dict]) -> list[dict]:
    """Transparent engineering interpretations, deliberately separate from ML."""
    names = {item["parameter"] for item in affected}
    result = []
    if any(n.startswith("E1 EGT") for n in names) and any(n.startswith("E1 CHT") for n in names):
        result.append({"rule": "thermal_combustion", "interpretation": "Concurrent EGT and CHT deviation can indicate thermal or combustion stress.", "source": "configurable engineering advisory; not an ML fault prediction"})
    if "E1 OilP" in names and "E1 OilT" in names:
        result.append({"rule": "lubrication", "interpretation": "Concurrent oil-pressure and oil-temperature deviation warrants lubrication-system review.", "source": "configurable engineering advisory; not an ML fault prediction"})
    if "E1 RPM" in names and any(n.startswith("E1 EGT") for n in names):
        result.append({"rule": "combustion_performance", "interpretation": "RPM and EGT deviation together can indicate engine-performance or combustion instability.", "source": "configurable engineering advisory; not an ML fault prediction"})
    return result


def analyze_flight_window(flight_id: int, end_index: int | None = None, window: int = 120) -> dict:
    raw = data_service.get_flight_array(flight_id)
    df = flight_array_to_clean_df(raw)
    end = len(df) if end_index is None else max(1, min(int(end_index) + 1, len(df)))
    start = max(0, end - max(20, min(int(window), 2000)))
    frame = df.iloc[start:end]
    features = compute_flight_features(frame)
    anomaly = anomaly_service.predict_from_features(features)
    fault = fault_prediction_service.predict_from_features(features)
    health = health_index_service.compute_health_from_features(features, flight_id=flight_id)

    affected = []
    for parameter in SENSOR_PARAMETERS:
        key = f"{clean_key(parameter)}_mean"
        observed = features.get(key)
        baseline = get_baseline_stats(key) if model_bundle.scaler is not None else None
        if not _finite(observed) or baseline is None or baseline[1] <= 0:
            continue
        mean, std = baseline
        z = (float(observed) - mean) / std
        # A learned two-sigma comparison is reported only when the anomaly
        # model also flags the window, avoiding alerts from ordinary motion.
        if anomaly.get("anomaly_detected") and abs(z) >= 2.0:
            affected.append({
                "parameter": parameter, "observed_value": round(float(observed), 3),
                "expected_range": [round(mean - 2 * std, 3), round(mean + 2 * std, 3)],
                "deviation_percent": round((float(observed) - mean) / (abs(mean) + 1e-6) * 100, 2),
                "deviation_sigma": round(z, 2),
                "severity": "critical" if abs(z) >= 4 else "major" if abs(z) >= 3 else "warning",
            })
    affected.sort(key=lambda item: abs(item["deviation_sigma"]), reverse=True)

    valid_cells = int(frame[SENSOR_PARAMETERS].notna().sum().sum())
    sensor_quality = round(valid_cells / max(1, len(frame) * len(SENSOR_PARAMETERS)), 3)
    # This is an index, explicitly not a probability of mission success.
    anomaly_penalty = 15 if anomaly.get("anomaly_detected") else 0
    fault_penalty = 20 * float(fault.get("confidence") or 0) if fault.get("fault_detected") else 0
    reliability = round(max(0, min(100, health["health_score"] - anomaly_penalty - fault_penalty - (1 - sensor_quality) * 20)))
    status = "CRITICAL" if reliability < 40 else "WARNING" if reliability < 75 else "NORMAL"
    return {
        "flight_id": flight_id, "data_source": "NGAFID historical telemetry window",
        "window": {"start_index": start, "end_index": end - 1, "samples": len(frame)},
        "anomaly": anomaly, "fault_prediction": fault, "health": health,
        "affected_parameters": affected[:8], "engineering_advisories": _advisories(affected),
        "sensor_quality": sensor_quality,
        "mission_reliability_index": reliability, "risk_level": status,
        "reliability_note": "Mission Reliability Index is a prototype index linked to windowed ML outputs and sensor completeness; it is not a validated probability of mission success.",
    }
