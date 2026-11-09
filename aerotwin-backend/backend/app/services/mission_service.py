"""
app/services/mission_service.py
=================================
"Mission simulation" (POST /api/missions/simulate) is different from
"Mission replay" (GET /api/replay/{flight_id}):

  - Replay plays back a real historical flight's telemetry, unmodified.
  - Simulation takes a real historical flight as a TEMPLATE, optionally
    perturbs it (stress_factor on load-related channels, duration_scale
    on how far through the profile we look), and runs the trained
    models at several checkpoints to produce a predicted health
    trajectory for a hypothetical mission.

*** This is a documented, heuristic "what-if" tool for the demo -
NOT a physics-based flight/engine simulator. Perturbations are simple
multiplications of real sensor values, not a simulation of actual
engine thermodynamics. *** SETUP_GUIDE.md says so explicitly.
"""

from __future__ import annotations

import logging
from typing import Dict

import numpy as np
import pandas as pd

from app.services import fault_prediction_service, health_index_service
from app.services.data_service import data_service
from app.services.feature_engineering import compute_flight_features
from app.services.preprocessing import flight_array_to_clean_df
from app.utils.db import save_mission

logger = logging.getLogger(__name__)

# Channels treated as "load-bearing" - scaled by stress_factor to simulate a
# more/less demanding mission profile. Everything else (environment, fuel
# quantity, battery) is left as recorded in the template flight.
STRESS_CHANNELS = [
    "E1 RPM", "E1 EGT1", "E1 EGT2", "E1 EGT3", "E1 EGT4",
    "E1 CHT1", "E1 CHT2", "E1 CHT3", "E1 CHT4", "E1 FFlow",
]

CHECKPOINTS = [0.2, 0.4, 0.6, 0.8, 1.0]


def _apply_stress(df: pd.DataFrame, stress_factor: float) -> pd.DataFrame:
    if stress_factor == 1.0:
        return df
    perturbed = df.copy()
    for ch in STRESS_CHANNELS:
        if ch in perturbed.columns:
            perturbed[ch] = perturbed[ch] * stress_factor
    return perturbed


def simulate_mission(base_flight_id: int, name: str, duration_scale: float, stress_factor: float) -> dict:
    raw = data_service.get_flight_array(base_flight_id)
    df = flight_array_to_clean_df(raw)
    df = _apply_stress(df, stress_factor)

    # duration_scale is illustrative: it changes how much of the (stress-
    # perturbed) template profile we consider "the mission", capped to what
    # data we actually have. We do NOT synthesize new timesteps beyond the
    # template flight's real length - that would be fabricating sensor data.
    effective_len = min(len(df), max(10, int(len(df) * min(duration_scale, 1.0))))
    df = df.iloc[:effective_len]

    trajectory = []
    for frac in CHECKPOINTS:
        cutoff = max(5, int(effective_len * frac))
        window = df.iloc[:cutoff]
        features = compute_flight_features(window)
        health = health_index_service.compute_health_from_features(features)
        trajectory.append(
            {
                "checkpoint": frac,
                "predicted_health_score": health["health_score"],
                "predicted_status": health["health_status"],
            }
        )

    final_features = compute_flight_features(df)
    fault_prediction = fault_prediction_service.predict_from_features(final_features)

    worst_status = min(
        trajectory, key=lambda s: {"HEALTHY": 2, "WARNING": 1, "CRITICAL": 0}[s["predicted_status"]]
    )["predicted_status"]
    # Vocabulary matches the frontend's health.riskLevel convention
    # (src/data/mockUAVData.js uses LOW / MODERATE / HIGH).
    overall_risk = {"HEALTHY": "LOW", "WARNING": "MODERATE", "CRITICAL": "HIGH"}[worst_status]

    params = {"duration_scale": duration_scale, "stress_factor": stress_factor}
    result = {
        "base_flight_id": base_flight_id,
        "name": name,
        "params": params,
        "predicted_trajectory": trajectory,
        "overall_risk": overall_risk,
        "fault_prediction": fault_prediction,
        "is_prototype": True,
        "note": (
            "Prototype what-if mission simulation: uses a real NGAFID flight as a template, "
            "with simple multiplicative stress perturbation on load-related channels, then runs "
            "the trained anomaly/fault/health models at several checkpoints. Not a physics-based "
            "flight simulator."
        ),
    }

    mission_id = save_mission(name, base_flight_id, params, result)
    result["mission_id"] = mission_id
    return result
