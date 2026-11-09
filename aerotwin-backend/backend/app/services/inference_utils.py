"""
app/services/inference_utils.py
=================================
Tiny shared helpers used by anomaly_service.py, fault_prediction_service.py,
health_index_service.py, and manual_input_service.py so there's exactly one
place that decides how a feature dict becomes the ordered NumPy vector the
models expect, and one place that knows how to look up a feature's
training-set baseline (mean/std) from the saved StandardScaler.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

import numpy as np

from app.models.model_loader import model_bundle


def vectorize_features(features: Dict[str, float]) -> Optional[np.ndarray]:
    """Aligns an arbitrary feature dict to model_bundle.feature_columns order,
    filling missing/NaN entries with 0.0. Features are z-scored by the saved
    StandardScaler, so 0.0-before-scaling is a documented, neutral choice
    for "this sensor/derived feature was unavailable for this flight" -
    see ml/train_anomaly_model.py and ml/train_fault_model.py."""
    if not model_bundle.feature_columns:
        return None
    row = []
    for col in model_bundle.feature_columns:
        val = features.get(col, np.nan)
        row.append(0.0 if val is None or (isinstance(val, float) and np.isnan(val)) else val)
    return np.array(row, dtype=np.float64).reshape(1, -1)


def get_baseline_stats(feature_name: str) -> Optional[Tuple[float, float]]:
    """Returns (mean, std) for one named feature, straight from the trained
    StandardScaler - i.e. "what does a typical training-set flight look like
    on this dimension". Returns None if models aren't trained yet or the
    feature isn't one the models use."""
    if not model_bundle.feature_columns or model_bundle.scaler is None:
        return None
    mean_ = getattr(model_bundle.scaler, "mean_", None)
    scale_ = getattr(model_bundle.scaler, "scale_", None)
    if mean_ is None or scale_ is None:
        return None
    try:
        idx = model_bundle.feature_columns.index(feature_name)
    except ValueError:
        return None
    std = float(scale_[idx]) if scale_[idx] != 0 else 1e-6
    return float(mean_[idx]), std


def get_all_baseline_means() -> Dict[str, float]:
    """Every trained feature's baseline mean, keyed by feature name. Used to
    build a 'perfectly average flight' starting point - see
    manual_input_service.py."""
    if not model_bundle.feature_columns or model_bundle.scaler is None:
        return {}
    mean_ = getattr(model_bundle.scaler, "mean_", None)
    if mean_ is None:
        return {}
    return {col: float(mean_[i]) for i, col in enumerate(model_bundle.feature_columns)}
