"""
app/models/model_loader.py
============================
Lazily loads the trained model artifacts produced by the ml/ scripts:

    models/anomaly_model.pkl     - sklearn IsolationForest
    models/fault_model.pkl       - sklearn RandomForestClassifier
    models/scaler.pkl            - sklearn StandardScaler (fit on training features)
    models/label_encoder.pkl     - sklearn LabelEncoder (fault label <-> int)
    models/feature_columns.json  - ordered list of feature names the models expect

Everything here is defensive: if a file doesn't exist yet (you haven't
run ml/train_*.py), the loader just returns None and sets a status flag,
instead of crashing the whole API. This lets you demo the read-only
parts of the API (flights, telemetry, replay) before training is done.
"""

import json
import logging
from typing import Any, List, Optional

import joblib

from app.config import settings

logger = logging.getLogger(__name__)


class ModelBundle:
    def __init__(self):
        self.anomaly_model: Optional[Any] = None
        self.fault_model: Optional[Any] = None
        self.scaler: Optional[Any] = None
        self.label_encoder: Optional[Any] = None
        self.feature_columns: List[str] = []
        self.metrics: dict = {}
        self.load()

    def load(self) -> None:
        self.anomaly_model = self._safe_load(settings.ANOMALY_MODEL_PATH)
        self.fault_model = self._safe_load(settings.FAULT_MODEL_PATH)
        self.scaler = self._safe_load(settings.SCALER_PATH)
        self.label_encoder = self._safe_load(settings.LABEL_ENCODER_PATH)

        if settings.FEATURE_COLUMNS_PATH.exists():
            try:
                with open(settings.FEATURE_COLUMNS_PATH, "r", encoding="utf-8") as f:
                    self.feature_columns = json.load(f)
            except (OSError, json.JSONDecodeError) as exc:
                logger.error("Could not read feature_columns.json: %s", exc)
                self.feature_columns = []
        else:
            self.feature_columns = []

        if settings.METRICS_PATH.exists():
            try:
                with open(settings.METRICS_PATH, "r", encoding="utf-8") as f:
                    self.metrics = json.load(f)
            except (OSError, json.JSONDecodeError):
                self.metrics = {}

    def _safe_load(self, path):
        if not path.exists():
            logger.warning(
                "Model artifact not found: %s (train it with the scripts in ml/, "
                "see SETUP_GUIDE.md)", path
            )
            return None
        try:
            return joblib.load(path)
        except Exception as exc:  # noqa: BLE001 - want to keep the server alive either way
            logger.error("Failed to load model artifact %s: %s", path, exc)
            return None

    def reload(self) -> None:
        logger.info("Reloading model artifacts from disk...")
        self.load()

    @property
    def anomaly_ready(self) -> bool:
        return self.anomaly_model is not None and self.scaler is not None

    @property
    def fault_ready(self) -> bool:
        return (
            self.fault_model is not None
            and self.scaler is not None
            and self.label_encoder is not None
            and len(self.feature_columns) > 0
        )


# Module-level singleton
model_bundle = ModelBundle()
