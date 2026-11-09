"""
app/api/routes_faults.py
==========================
    GET /api/flights/{flight_id}/faults   - predicted (+ actual, if labelled) fault info
    GET /api/faults/labels                 - reference list of fault labels the model knows
"""

import logging

from fastapi import APIRouter

from app.models.model_loader import model_bundle
from app.models.schemas import FlightFaultsResponse
from app.services import fault_prediction_service
from app.services.data_service import data_service
from app.utils.errors import handle_service_errors

logger = logging.getLogger(__name__)
router = APIRouter(tags=["faults"])


@router.get("/flights/{flight_id}/faults", response_model=FlightFaultsResponse)
def get_flight_faults(flight_id: int):
    with handle_service_errors():
        row = data_service.header_row(flight_id)
        prediction = fault_prediction_service.predict_for_flight(flight_id)

    actual_label = row.get("label")
    if actual_label is not None and str(actual_label).lower() == "nan":
        actual_label = None

    return FlightFaultsResponse(
        flight_id=flight_id,
        actual_label=actual_label,
        fault_detected=prediction.get("fault_detected", False),
        fault_type=prediction.get("fault_type"),
        confidence=prediction.get("confidence"),
        severity=prediction.get("severity"),
        recommended_action=prediction.get("recommended_action"),
        uav_component=prediction.get("uav_component"),
        alert=prediction.get("alert", False),
        model_status=prediction.get("model_status"),
        candidate_fault_type=prediction.get("candidate_fault_type"),
        candidate_confidence=prediction.get("candidate_confidence"),
        validation_note=prediction.get("validation_note"),
    )


@router.get("/faults/labels")
def get_fault_labels():
    """Reference endpoint: the exact fault label strings the trained classifier
    can predict - i.e. exactly the labels seen in flight_header.csv during
    training. Useful for building a legend/filter in the frontend."""
    if not model_bundle.fault_ready or model_bundle.label_encoder is None:
        return {
            "model_status": "NOT_TRAINED",
            "labels": [],
            "note": "Train the fault classifier first: python ml/train_fault_model.py",
        }
    labels = list(model_bundle.label_encoder.classes_)
    return {"model_status": "OK", "labels": labels, "count": len(labels)}
