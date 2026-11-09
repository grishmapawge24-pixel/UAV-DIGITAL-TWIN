"""
app/services/anomaly_service.py
=================================
Thin wrapper around the trained Isolation Forest anomaly model.

Handles:
  - turning a flight_id (or a raw feature dict) into the exact ordered
    feature vector the model was trained on
  - imputing missing/NaN features the same way training did (median
    imputation values are saved alongside the scaler at training time)
  - returning a simple, demo-friendly anomaly_detected / anomaly_score pair

If no model has been trained yet, `predict()` returns a clear
"model_status": "NOT_TRAINED" response instead of raising - so the rest
of the API keeps working during development.
"""

from __future__ import annotations

import logging
from typing import Dict

from app.models.model_loader import model_bundle
from app.services.feature_engineering import get_features_for_flight
from app.services.inference_utils import vectorize_features

logger = logging.getLogger(__name__)


def predict_from_features(features: Dict[str, float]) -> dict:
    if not model_bundle.anomaly_ready:
        return {
            "anomaly_detected": False,
            "anomaly_score": None,
            "threshold": None,
            "model_status": "NOT_TRAINED",
        }

    vec = vectorize_features(features)
    if vec is None:
        return {
            "anomaly_detected": False,
            "anomaly_score": None,
            "threshold": None,
            "model_status": "NOT_TRAINED",
        }

    scaled = model_bundle.scaler.transform(vec)
    # IsolationForest: decision_function > 0 => inlier (normal), < 0 => outlier (anomaly).
    # We flip the sign so a HIGHER anomaly_score means MORE anomalous - more
    # intuitive for a dashboard than sklearn's raw convention.
    raw_score = float(model_bundle.anomaly_model.decision_function(scaled)[0])
    anomaly_score = round(-raw_score, 4)
    prediction = int(model_bundle.anomaly_model.predict(scaled)[0])  # -1 = anomaly, 1 = normal

    return {
        "anomaly_detected": prediction == -1,
        "anomaly_score": anomaly_score,
        "threshold": 0.0,
        "model_status": "OK",
    }


def predict_for_flight(flight_id: int) -> dict:
    features = get_features_for_flight(flight_id)
    return predict_from_features(features)
