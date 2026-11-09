"""
app/services/manual_input_service.py
======================================
Powers POST /api/manual/evaluate: the user types in CURRENT engine
parameter readings by hand (no flight_id, no time series) and gets back
a real AI comparison against the trained models - not just a static
"is this within limits" range check.

*** UNITS: this endpoint expects values in NGAFID's native units -
RPM, °F for CHT/EGT/OilT, psi for OilP, gal/hr for fuel flow, volts for
battery. (NGAFID is a US-based dataset; these are the conventional
units for this kind of aircraft telemetry.) If your frontend displays
°C/bar/L-per-hr, convert to these units client-side before calling this
endpoint - see the frontend's src/utils/unitConversions.js. ***

HOW A SINGLE SNAPSHOT GETS COMPARED TO MODELS TRAINED ON WHOLE FLIGHTS
------------------------------------------------------------------------
The anomaly/fault models were trained on per-flight AGGREGATE features
(mean, std, min, max, slope, etc. over an entire flight's time series).
A manual entry only gives us ONE moment's readings - there's no time
series to compute std/slope/etc. from.

Rather than feed the models a bunch of zeros for everything we don't
know (which would look like a bizarre, flat-lined, impossible flight),
we start from **the training set's baseline mean for every single
feature** - i.e. "assume an otherwise completely average, typical
flight" - and then overlay ONLY the `_mean` feature(s) that correspond
to parameters the user actually typed in. This asks the models a
well-posed question: *"for an otherwise normal flight, does THIS
particular RPM/CHT/EGT/... value look anomalous or fault-associated?"*

This is still a documented simplification (see the class docstring for
health_index_service.py) - it cannot see trends or variability, only
levels - but it is a much more honest and stable basis for comparison
than zero-filling every unknown feature.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from app.services import anomaly_service, fault_prediction_service
from app.services.feature_engineering import clean_key
from app.services.inference_utils import get_all_baseline_means, get_baseline_stats
from app.utils.sensor_mapping import SENSOR_PARAMETERS

# Simple/common fields -> which raw NGAFID sensor channel(s) they set.
# CHT/EGT are broadcast to all 4 cylinders since a manual form typically
# collects one representative reading; use `advanced_parameters` (exact
# SENSOR_PARAMETERS names, e.g. "E1 CHT2") to set individual cylinders.
SIMPLE_FIELD_MAP: Dict[str, List[str]] = {
    "rpm": ["E1 RPM"],
    "cht": ["E1 CHT1", "E1 CHT2", "E1 CHT3", "E1 CHT4"],
    "egt": ["E1 EGT1", "E1 EGT2", "E1 EGT3", "E1 EGT4"],
    "oil_pressure": ["E1 OilP"],
    "oil_temperature": ["E1 OilT"],
    "fuel_flow": ["E1 FFlow"],
    "battery_voltage": ["volt1", "volt2"],
}

# Deviation-from-baseline thresholds (documented heuristic, consistent with
# health_index_service.py's z-score based deviation signal).
Z_WARNING = 1.0
Z_MAJOR = 2.0
Z_CRITICAL = 3.5


def resolve_channel_values(payload: dict) -> Dict[str, float]:
    """Turns the request payload into {SENSOR_PARAMETERS channel: value},
    covering only channels the user actually specified (simple fields +
    advanced_parameters overrides, advanced wins on conflict)."""
    resolved: Dict[str, float] = {}

    for field, channels in SIMPLE_FIELD_MAP.items():
        val = payload.get(field)
        if val is not None:
            for ch in channels:
                resolved[ch] = float(val)

    advanced = payload.get("advanced_parameters") or {}
    for ch, val in advanced.items():
        if ch in SENSOR_PARAMETERS and val is not None:
            resolved[ch] = float(val)

    return resolved


def build_snapshot_features(resolved_values: Dict[str, float]) -> Dict[str, float]:
    """Baseline-anchored feature vector - see module docstring. Every
    feature starts at the trained StandardScaler's mean (a "perfectly
    average flight"); only the `_mean` features for user-specified
    channels are overridden."""
    features = get_all_baseline_means()  # {} if models aren't trained yet
    for channel, value in resolved_values.items():
        features[f"{clean_key(channel)}_mean"] = value
    return features


def _status_for_z(z: float) -> str:
    az = abs(z)
    if az <= Z_WARNING:
        return "normal"
    if az <= Z_MAJOR:
        return "warning"
    if az <= Z_CRITICAL:
        return "major"
    return "critical"


def compare_parameters(resolved_values: Dict[str, float]) -> List[dict]:
    """Per-parameter deviation-from-baseline comparison, independent of the
    ML classifiers - direct, explainable feedback for each value the user
    typed in. Only covers channels the user actually provided."""
    comparisons = []
    seen_keys = set()

    for channel, value in resolved_values.items():
        key = f"{clean_key(channel)}_mean"
        if key in seen_keys:
            continue
        seen_keys.add(key)

        baseline = get_baseline_stats(key)
        if baseline is None:
            comparisons.append(
                {
                    "parameter": channel,
                    "value": value,
                    "baseline_mean": None,
                    "baseline_std": None,
                    "deviation_sigma": None,
                    "status": "offline",
                    "direction": None,
                }
            )
            continue

        mean, std = baseline
        z = (value - mean) / std
        comparisons.append(
            {
                "parameter": channel,
                "value": value,
                "baseline_mean": round(mean, 2),
                "baseline_std": round(std, 2),
                "deviation_sigma": round(z, 2),
                "status": _status_for_z(z),
                "direction": "high" if z > 0.1 else "low" if z < -0.1 else None,
            }
        )

    return comparisons


def _manual_health_from_comparisons(
    parameter_comparison: List[dict], fault_result: dict, anomaly_result: dict
) -> Tuple[int, str]:
    """Overall health score/status for a manual snapshot.

    Deliberately NOT the same formula as health_index_service.py's per-flight
    scoring. That formula splits weight across anomaly/fault/deviation/trend
    signals, which works well when several concurrent signals from a REAL
    flight's full time series are usually all somewhat informative. For a
    manual single-moment snapshot, the ML classifiers often can't confidently
    react to a single extreme value overlaid on an otherwise perfectly-average
    baseline (verified empirically during development: an extreme oil-pressure
    override barely moved the fault classifier's output at all) - so this
    anchors primarily on the direct per-parameter deviation, the one signal
    that reliably reacts. The fault/anomaly models still get a secondary,
    score-reducing (never score-increasing) vote when they DO fire.
    """
    z_values = [abs(c["deviation_sigma"]) for c in parameter_comparison if c["deviation_sigma"] is not None]
    worst_z = max(z_values) if z_values else 0.0

    # Piecewise-linear, anchored to the same Z_WARNING/Z_MAJOR/Z_CRITICAL
    # thresholds used for each parameter's individual status label, so a
    # parameter shown as "critical" always corresponds to a score deep in
    # the CRITICAL band below.
    if worst_z <= Z_WARNING:
        score = 100 - (worst_z / Z_WARNING) * 10                                    # 90-100
    elif worst_z <= Z_MAJOR:
        score = 90 - (worst_z - Z_WARNING) / (Z_MAJOR - Z_WARNING) * 25             # 65-90
    elif worst_z <= Z_CRITICAL:
        score = 65 - (worst_z - Z_MAJOR) / (Z_CRITICAL - Z_MAJOR) * 30              # 35-65
    else:
        score = max(5.0, 35 - min(worst_z - Z_CRITICAL, 5.0) * 6)                    # 5-35

    if fault_result.get("model_status") == "OK" and fault_result.get("fault_detected"):
        confidence = fault_result.get("confidence") or 0.0
        severity_weight = {"critical": 25, "major": 15, "warning": 8}.get(fault_result.get("severity"), 10)
        score -= confidence * severity_weight

    if anomaly_result.get("model_status") == "OK" and anomaly_result.get("anomaly_detected"):
        score -= 8

    score = round(max(0.0, min(100.0, score)))

    if score >= 75:
        status = "HEALTHY"
    elif score >= 40:
        status = "WARNING"
    else:
        status = "CRITICAL"

    return score, status


def _worst_comparison(parameter_comparison: List[dict]) -> Optional[dict]:
    scored = [c for c in parameter_comparison if c["deviation_sigma"] is not None]
    if not scored:
        return None
    return max(scored, key=lambda c: abs(c["deviation_sigma"]))


def evaluate_manual_parameters(payload: dict) -> dict:
    resolved_values = resolve_channel_values(payload)
    features = build_snapshot_features(resolved_values)

    anomaly_result = anomaly_service.predict_from_features(features)
    fault_result = fault_prediction_service.predict_from_features(features)
    parameter_comparison = compare_parameters(resolved_values)
    health_score, health_status = _manual_health_from_comparisons(
        parameter_comparison, fault_result, anomaly_result
    )

    model_status = fault_result.get("model_status", "NOT_TRAINED")
    note = (
        "Snapshot compared against a baseline-anchored 'typical flight' feature vector for "
        "the fault/anomaly models, and directly against the training-set mean/std for the "
        "per-parameter comparison (the more reliable signal for a single-moment reading - "
        "see app/services/manual_input_service.py). Values not provided are assumed to be "
        "at the training-set average."
        if model_status == "OK"
        else "Models are not trained yet, so this returns only the raw values you entered "
        "with no AI comparison. Train the models first (see SETUP_GUIDE.md)."
    )

    fault_detected = fault_result.get("fault_detected", False)
    fault_type = fault_result.get("fault_type")
    confidence = fault_result.get("confidence")
    severity = fault_result.get("severity")
    recommended_action = fault_result.get("recommended_action")
    uav_component = fault_result.get("uav_component")
    alert = fault_result.get("alert", False)

    # The trained classifier only ever names a REAL historical fault label, and
    # (as documented above) may stay quiet even when one parameter is wildly
    # off-baseline. So when it doesn't fire but a parameter is flagged
    # 'critical'/'major' directly, still tell the frontend which subsystem to
    # highlight and what to check - WITHOUT inventing a fault_type/confidence,
    # since that would misrepresent a threshold flag as a learned classification.
    if not fault_detected:
        worst = _worst_comparison(parameter_comparison)
        if worst and worst["status"] in ("critical", "major"):
            uav_component = fault_prediction_service.classify_component(worst["parameter"])
            severity = worst["status"]
            recommended_action = fault_prediction_service.recommend_action(worst["parameter"])
            alert = True
            note += (
                f" No specific historical fault pattern matched, but {worst['parameter']} is "
                f"{abs(worst['deviation_sigma']):.1f}\u03c3 from baseline - flagging the affected "
                f"subsystem directly from the parameter itself, not from a predicted fault label."
            )

    return {
        "parameters_provided": sorted(resolved_values.keys()),
        "parameter_comparison": parameter_comparison,
        "health_score": health_score,
        "health_status": health_status,
        "anomaly_detected": anomaly_result.get("anomaly_detected", False),
        "anomaly_score": anomaly_result.get("anomaly_score"),
        "fault_detected": fault_detected,
        "fault_type": fault_type,
        "confidence": confidence,
        "severity": severity,
        "recommended_action": recommended_action,
        "uav_component": uav_component,
        "alert": alert,
        "model_status": model_status,
        "note": note,
    }
