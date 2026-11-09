"""
app/api/routes_predictions.py
===============================
    POST /api/predict   - fault classification, given a flight_id or a raw feature vector
    POST /api/anomaly    - anomaly detection, given a flight_id or a raw feature vector
"""

import logging

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    AnomalyRequest,
    AnomalyResponse,
    ManualEvaluationResponse,
    ManualParametersRequest,
    PredictRequest,
    PredictResponse,
)
from app.services import anomaly_service, fault_prediction_service, manual_input_service
from app.services.feature_engineering import get_features_for_flight
from app.utils.errors import handle_service_errors

logger = logging.getLogger(__name__)
router = APIRouter(tags=["predictions"])


def _resolve_features(flight_id, features):
    if features:
        return features
    if flight_id is not None:
        with handle_service_errors():
            return get_features_for_flight(flight_id)
    raise HTTPException(status_code=400, detail="Provide either 'flight_id' or 'features' in the request body.")


@router.post("/predict", response_model=PredictResponse)
def predict_fault(request: PredictRequest):
    features = _resolve_features(request.flight_id, request.features)
    result = fault_prediction_service.predict_from_features(features)
    return PredictResponse(**result)


@router.post("/anomaly", response_model=AnomalyResponse)
def predict_anomaly(request: AnomalyRequest):
    features = _resolve_features(request.flight_id, request.features)
    result = anomaly_service.predict_from_features(features)
    return AnomalyResponse(**result)


@router.post("/manual/evaluate", response_model=ManualEvaluationResponse)
def evaluate_manual_parameters(request: ManualParametersRequest):
    """Type in current engine readings by hand (no flight_id needed) and get
    a real AI comparison against the trained models - see
    app/services/manual_input_service.py for exactly how this works and
    its documented limitations."""
    result = manual_input_service.evaluate_manual_parameters(request.model_dump())
    return ManualEvaluationResponse(**result)
