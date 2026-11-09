"""
app/services/health_index_service.py
======================================
Computes a 0-100 "engine health score" + HEALTHY / WARNING / CRITICAL
status for a flight.

*** THIS IS EXPLICITLY A PROTOTYPE HEURISTIC, NOT A CERTIFIED METRIC. ***
There is no ground-truth "health score" label anywhere in NGAFID to
train against, so this is a documented, hand-weighted combination of
signals the trained models DO give us:

  1. Anomaly signal   - IsolationForest anomaly_score for the flight
  2. Fault signal      - fault classifier confidence + heuristic severity
  3. Deviation signal  - how far this flight's *_mean features are, in
                          standard deviations, from the StandardScaler's
                          training-set mean/std (i.e. "how unusual is
                          this flight compared to the training data")
  4. Trend signal      - magnitude of *_slope features for key health
                          channels (a fast rising CHT/EGT or falling
                          OilP within a single flight is worth flagging)

Weights below are simple constants, tuned to "look reasonable" for a
demo, NOT fitted from data. SETUP_GUIDE.md and the README say this
explicitly so nobody presents this score as scientifically validated.
"""

from __future__ import annotations

import math
from typing import Dict, List

from app.config import settings
from app.models.model_loader import model_bundle
from app.services import anomaly_service, fault_prediction_service
from app.services.feature_engineering import get_features_for_flight
from app.services.inference_utils import get_baseline_stats

# --- tunable weights (documented, not learned) -----------------------------
W_ANOMALY = 30      # max points lost to a strong anomaly signal
W_FAULT = 40         # max points lost to a high-confidence, high-severity fault
W_DEVIATION = 20     # max points lost to features far from the training baseline
W_TREND = 10         # max points lost to a strong within-flight trend

DEVIATION_Z_CAP = 4.0   # z-scores beyond this are treated as "maximally deviant"
TREND_CHANNELS = [
    "E1_OilP_slope", "E1_OilT_slope", "E1_RPM_slope",
    "E1_CHT1_slope", "E1_CHT2_slope", "E1_CHT3_slope", "E1_CHT4_slope",
    "E1_EGT1_slope", "E1_EGT2_slope", "E1_EGT3_slope", "E1_EGT4_slope",
]
TREND_SLOPE_CAP = 1.0  # units/timestep magnitude treated as "maximally trending"; tune per demo data


def _deviation_score(features: Dict[str, float]) -> tuple:
    """Returns (0-1 severity, list of human-readable factor strings)."""
    if not model_bundle.feature_columns or model_bundle.scaler is None:
        return 0.0, []

    z_scores = []
    for col in model_bundle.feature_columns:
        if not col.endswith("_mean"):
            continue
        val = features.get(col)
        if val is None or (isinstance(val, float) and math.isnan(val)):
            continue  # unavailable sensor - never counted as "deviating"
        baseline = get_baseline_stats(col)
        if baseline is None:
            continue
        mean, std = baseline
        z = abs((val - mean) / std)
        z_scores.append((col, z))

    if not z_scores:
        return 0.0, []

    z_scores.sort(key=lambda t: t[1], reverse=True)
    top = z_scores[:3]
    avg_top_z = sum(z for _, z in top) / len(top)
    severity = min(avg_top_z, DEVIATION_Z_CAP) / DEVIATION_Z_CAP

    factors = [
        f"{col.replace('_mean', '')} is {z:.1f}\u03c3 from the training baseline"
        for col, z in top if z > 1.5
    ]
    return severity, factors


def _trend_score(features: Dict[str, float]) -> tuple:
    magnitudes = []
    factors: List[str] = []
    for col in TREND_CHANNELS:
        val = features.get(col)
        if val is None or (isinstance(val, float) and math.isnan(val)):
            continue
        magnitudes.append(abs(val))
        if abs(val) > TREND_SLOPE_CAP * 0.5:
            direction = "rising" if val > 0 else "falling"
            factors.append(f"{col.replace('_slope', '')} is {direction} within this flight")

    if not magnitudes:
        return 0.0, []

    severity = min(max(magnitudes), TREND_SLOPE_CAP) / TREND_SLOPE_CAP
    return severity, factors[:2]


def compute_health_from_features(features: Dict[str, float], flight_id: int = None) -> dict:
    """Core scoring logic, decoupled from where the features came from - a
    real flight (compute_health_for_flight) or a perturbed what-if scenario
    (mission simulation, see mission_service.py)."""
    anomaly_result = anomaly_service.predict_from_features(features)
    fault_result = fault_prediction_service.predict_from_features(features)
    deviation_severity, deviation_factors = _deviation_score(features)
    trend_severity, trend_factors = _trend_score(features)

    score = 100.0
    factors: List[str] = []

    if anomaly_result.get("model_status") == "OK" and anomaly_result.get("anomaly_detected"):
        raw = anomaly_result.get("anomaly_score") or 0.0
        # anomaly_score from IsolationForest is typically small (roughly -0.2..0.5);
        # squash into 0..1 with a simple clipped scale for a demo-stable deduction.
        norm = min(max(raw, 0.0), 0.5) / 0.5
        deduction = W_ANOMALY * norm
        score -= deduction
        factors.append(f"Anomaly detected (score {raw:.3f})")

    if fault_result.get("model_status") == "OK" and fault_result.get("fault_detected"):
        confidence = fault_result.get("confidence") or 0.0
        severity_weight = {"critical": 1.0, "major": 0.6, "warning": 0.3}.get(fault_result.get("severity"), 0.5)
        deduction = W_FAULT * confidence * severity_weight
        score -= deduction
        factors.append(
            f"Predicted fault: {fault_result.get('fault_type')} "
            f"(confidence {confidence:.2f}, severity {fault_result.get('severity')})"
        )

    if deviation_severity > 0:
        score -= W_DEVIATION * deviation_severity
        factors.extend(deviation_factors)

    if trend_severity > 0:
        score -= W_TREND * trend_severity
        factors.extend(trend_factors)

    score = round(max(0.0, min(100.0, score)))

    if score >= settings.HEALTH_THRESHOLD_WARNING:
        status = "HEALTHY"
    elif score >= settings.HEALTH_THRESHOLD_CRITICAL:
        status = "WARNING"
    else:
        status = "CRITICAL"

    if not factors:
        factors.append("No significant anomaly, fault, deviation, or trend signals detected.")

    return {
        "flight_id": flight_id,
        "health_score": score,
        "health_status": status,
        "anomaly_detected": bool(anomaly_result.get("anomaly_detected")),
        "anomaly_score": anomaly_result.get("anomaly_score"),
        "contributing_factors": factors,
        "is_prototype": True,
        "note": (
            "Prototype health index: a documented, hand-weighted heuristic combining "
            "the anomaly model, fault classifier, deviation-from-baseline, and within-flight "
            "trend signals. Not a certified airworthiness or maintenance metric."
        ),
    }


def compute_health_for_flight(flight_id: int) -> dict:
    features = get_features_for_flight(flight_id)
    return compute_health_from_features(features, flight_id=flight_id)
