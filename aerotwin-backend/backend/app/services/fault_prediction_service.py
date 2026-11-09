"""
app/services/fault_prediction_service.py
==========================================
Wraps the trained Random Forest fault classifier.

The model only ever predicts labels it was trained on - i.e. actual
fault strings found in flight_header.csv's `label`/`target_class`
column (e.g. "intake gasket leak/damage"). We never invent new fault
names.

On top of the raw model prediction we add three small, RULE-BASED,
clearly-heuristic layers (documented as such, not claimed to be
data-driven):

  1. severity        - keyword match on the predicted label + how
                        confident the model is
  2. uav_component    - keyword match, for the frontend's 3D UAV highlight
  3. recommended_action - generic maintenance guidance per keyword

These three exist purely to make the demo/frontend useful (severity
badge, 3D subsystem highlight, a sentence of advice) - they are NOT
learned from data and SETUP_GUIDE.md says so explicitly.

VOCABULARY NOTE: `severity` values ('warning' | 'major' | 'critical')
and `uav_component` ids ('engine', 'fuelSystem', 'coolingSystem',
'lubricationSystem', 'electricalSystem', 'battery', 'propeller',
'sensors', 'avionics') are deliberately copied from the actual React
frontend's src/utils/status.js and src/data/uavProfiles.js, so the
API response can be rendered with the frontend's existing badge/status-dot
CSS and 3D component-highlight logic with zero translation layer.
"""

from __future__ import annotations

import logging
import json
from typing import Dict, Optional

import numpy as np

from app.models.model_loader import model_bundle
from app.services.feature_engineering import get_features_for_flight
from app.services.inference_utils import vectorize_features

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Heuristic lookup tables. Keys are matched as case-insensitive substrings
# against the predicted fault label. First match wins; order matters.
#
# uav_component values match src/data/uavProfiles.js's `uavComponents` ids
# exactly (engine, fuelSystem, coolingSystem, lubricationSystem,
# electricalSystem, battery, propeller, sensors, avionics).
# ---------------------------------------------------------------------------
_COMPONENT_KEYWORDS = [
    (("battery",), "battery"),
    (("volt", "amp", "alternator", "electrical"), "electricalSystem"),
    (("fuel", "fqty", "flow", "injector"), "fuelSystem"),
    (("oil", "lubrication"), "lubricationSystem"),
    (("cht", "egt", "cylinder", "exhaust", "temperature", "overheat", "coolant", "cooling"), "coolingSystem"),
    (("prop", "propeller"), "propeller"),
    (("sensor",), "sensors"),
]

# severity values match src/utils/status.js's STATUS enum (warning/major/critical -
# there is no separate "low" level for faults in the frontend's vocabulary).
_SEVERITY_KEYWORDS = [
    (("failure", "failed", "damage", "loss", "leak"), "critical"),
    (("fluctuation", "wear", "abnormal", "deviation", "drop", "degradation"), "major"),
]

_ACTION_KEYWORDS = [
    (("oil", "lubrication"), "Inspect oil system (pressure/temperature sensors, lines, and filter) before next flight."),
    (("gasket", "leak", "intake"), "Inspect intake system seals and gaskets for leaks before next mission."),
    (("fuel", "fqty", "flow", "injector"), "Inspect fuel delivery system (lines, pump, filters) and verify fuel quantity sensor readings."),
    (("volt", "amp", "battery", "alternator", "electrical"), "Inspect electrical/charging system (alternator output, battery health, wiring)."),
    (("cht", "egt", "overheat", "temperature", "coolant", "cooling"), "Inspect engine cooling and exhaust system; check for blocked baffles or sensor faults."),
    (("prop",), "Inspect propeller and related mounting hardware for damage or imbalance."),
]
_DEFAULT_ACTION = "Inspect the affected subsystem per the maintenance manual before next flight; consult qualified maintenance personnel."


def _validation_is_sufficient() -> bool:
    """Prevent a fault-only, weakly validated classifier from raising alerts."""
    from app.config import settings
    try:
        metrics = json.loads(settings.METRICS_PATH.read_text(encoding="utf-8"))
        return float(metrics["fault_model"].get("test_macro_f1", 0)) >= 0.50
    except (OSError, ValueError, KeyError, TypeError):
        return False


def _match_keywords(label: str, table) -> Optional[str]:
    label_lower = label.lower()
    for keywords, value in table:
        if any(k in label_lower for k in keywords):
            return value
    return None


def classify_component(label: str) -> str:
    return _match_keywords(label, _COMPONENT_KEYWORDS) or "engine"


def classify_severity(label: str, confidence: float) -> str:
    keyword_severity = _match_keywords(label, _SEVERITY_KEYWORDS)
    if keyword_severity == "critical":
        return "critical"
    if confidence >= 0.85:
        return keyword_severity or "critical"
    if confidence >= 0.6:
        return keyword_severity or "major"
    return keyword_severity or "warning"


def recommend_action(label: str) -> str:
    return _match_keywords(label, _ACTION_KEYWORDS) or _DEFAULT_ACTION


def predict_from_features(features: Dict[str, float]) -> dict:
    if not model_bundle.fault_ready:
        return {
            "fault_detected": False,
            "fault_type": None,
            "confidence": None,
            "severity": None,
            "recommended_action": None,
            "uav_component": None,
            "alert": False,
            "model_status": "NOT_TRAINED",
        }

    vec = vectorize_features(features)
    if vec is None:
        return {
            "fault_detected": False,
            "fault_type": None,
            "confidence": None,
            "severity": None,
            "recommended_action": None,
            "uav_component": None,
            "alert": False,
            "model_status": "NOT_TRAINED",
        }

    scaled = model_bundle.scaler.transform(vec)
    proba = model_bundle.fault_model.predict_proba(scaled)[0]
    top_idx = int(np.argmax(proba))
    confidence = float(proba[top_idx])
    label = model_bundle.label_encoder.inverse_transform([top_idx])[0]

    # Convention (documented in SETUP_GUIDE.md / ml/train_fault_model.py):
    # a "no fault" / "normal" class, if present in the training labels, is
    # matched by keyword; otherwise any predicted label counts as a detected
    # fault. This avoids assuming a specific label string exists.
    is_normal = any(k in str(label).lower() for k in ("normal", "no fault", "nominal", "none"))
    validation_sufficient = _validation_is_sufficient()
    # This dataset/model has no normal class. Expose the top class as a
    # research candidate, but do not assert a detected fault unless the
    # held-out multi-class metric is adequate.
    fault_detected = (not is_normal) and validation_sufficient

    severity = classify_severity(str(label), confidence) if fault_detected else None
    action = recommend_action(str(label)) if fault_detected else None
    component = classify_component(str(label)) if fault_detected else None

    return {
        "fault_detected": fault_detected,
        "fault_type": str(label) if fault_detected else None,
        "confidence": round(confidence, 4),
        "severity": severity,
        "recommended_action": action,
        "uav_component": component,
        "alert": fault_detected and severity in ("critical", "major"),
        "model_status": "OK" if validation_sufficient else "LIMITED_VALIDATION",
        "candidate_fault_type": str(label),
        "candidate_confidence": round(confidence, 4),
        "validation_note": None if validation_sufficient else (
            "Fault candidate withheld from alerting: held-out macro-F1 is below the 0.50 "
            "prototype deployment gate and training contains no normal class."
        ),
    }


def predict_for_flight(flight_id: int) -> dict:
    features = get_features_for_flight(flight_id)
    return predict_from_features(features)
