"""
app/api/routes_health.py
==========================
System-level endpoints:

    GET /api/health              - is the backend up, is data/models loaded?
    GET /api/engine/status        - current (demo) engine snapshot
    GET /api/dashboard/summary    - full dashboard payload for the frontend
    GET /api/sensors/available    - which sensors are really available, which aren't
"""

import logging

from fastapi import APIRouter, Query

from app.config import settings
from app.models.model_loader import model_bundle
from app.models.schemas import (
    DashboardSummary,
    HealthCheckResponse,
    SensorAvailability,
    SensorsAvailableResponse,
)
from app.services import fault_prediction_service, health_index_service
from app.services.data_service import DatasetNotConfiguredError, data_service
from app.services.feature_engineering import get_features_for_flight
from app.services.preprocessing import MappingNotVerifiedError
from app.utils.errors import handle_service_errors
from app.utils.sensor_mapping import (
    KNOWN_UNAVAILABLE_PARAMETERS,
    PARAMETER_GROUPS,
    SENSOR_PARAMETERS,
    sensor_mapping,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["system"])


def _param_group(param: str) -> str:
    for group, members in PARAMETER_GROUPS.items():
        if param in members:
            return group
    return "other"


def _pick_default_flight_id():
    if settings.DEMO_FLIGHT_ID is not None:
        return settings.DEMO_FLIGHT_ID
    try:
        ids = data_service.flight_ids()
        return ids[0] if ids else None
    except (DatasetNotConfiguredError, FileNotFoundError):
        return None


@router.get("/health", response_model=HealthCheckResponse)
def get_health():
    dataset_configured = settings.dataset_configured()
    header_loaded = False
    total_flights = None
    if dataset_configured:
        try:
            header = data_service.load_header()
            header_loaded = True
            total_flights = len(header)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not load flight_header.csv for /api/health: %s", exc)

    if not dataset_configured:
        message = (
            "NGAFID_DATA_PATH is not configured. Set it in backend/.env, then restart. "
            "See SETUP_GUIDE.md."
        )
    elif not header_loaded:
        message = "Dataset path is set but flight_header.csv could not be read. Check the path and filename."
    elif not sensor_mapping.usable:
        message = (
            "Dataset loaded, but the sensor column mapping is not verified yet. "
            "Run `python ml/verify_sensor_mapping.py` and confirm data/config/sensor_mapping.json."
        )
    elif not (model_bundle.anomaly_ready and model_bundle.fault_ready):
        message = "Dataset and mapping OK, but models are not trained yet. See SETUP_GUIDE.md training steps."
    else:
        message = "Backend fully configured: dataset loaded, mapping verified, models trained."

    return HealthCheckResponse(
        status="ok",
        app_name=settings.APP_NAME,
        dataset_configured=dataset_configured,
        dataset_path_exists=dataset_configured,
        flight_header_loaded=header_loaded,
        sensor_mapping_available=sensor_mapping.is_available,
        sensor_mapping_verified=sensor_mapping.is_verified,
        anomaly_model_loaded=model_bundle.anomaly_ready,
        fault_model_loaded=model_bundle.fault_ready,
        total_flights=total_flights,
        message=message,
    )


@router.get("/sensors/available", response_model=SensorsAvailableResponse)
def get_sensors_available():
    mapping_dict = sensor_mapping.as_dict()
    available = []
    for param in SENSOR_PARAMETERS:
        idx = sensor_mapping.get_index_for_name(param)
        available.append(
            SensorAvailability(
                parameter=param,
                group=_param_group(param),
                available=idx is not None,
                source_column_index=idx,
            )
        )
    return SensorsAvailableResponse(
        mapping_verified=sensor_mapping.is_verified,
        available_sensors=available,
        unavailable_sensors=KNOWN_UNAVAILABLE_PARAMETERS,
        note=(
            "available_sensors reflects the verified NGAFID column mapping. "
            "unavailable_sensors lists parameters requested by the SIH problem statement "
            "that NGAFID does not provide (e.g. vibration, injection timing) - these are "
            "never fabricated."
        ),
    )


def _build_dashboard(flight_id: int) -> DashboardSummary:
    with handle_service_errors():
        features = get_features_for_flight(flight_id)
        health = health_index_service.compute_health_for_flight(flight_id)
        fault = fault_prediction_service.predict_from_features(features)

    def g(key):
        v = features.get(key)
        return None if v is None else round(v, 2)

    return DashboardSummary(
        flight_id=flight_id,
        engine_health=health["health_score"],
        status=health["health_status"],
        rpm=g("E1_RPM_mean"),
        cht=g("E1_CHT1_mean"),
        egt=g("E1_EGT1_mean"),
        oil_pressure=g("E1_OilP_mean"),
        oil_temperature=g("E1_OilT_mean"),
        fuel_flow=g("E1_FFlow_mean"),
        battery_voltage=g("volt1_mean"),
        anomaly_detected=health["anomaly_detected"],
        fault_detected=fault.get("fault_detected", False),
        fault_type=fault.get("fault_type"),
        confidence=fault.get("confidence"),
        maintenance_recommendation=fault.get("recommended_action"),
        data_source="NGAFID historical telemetry",
        unavailable_parameters=KNOWN_UNAVAILABLE_PARAMETERS,
    )


@router.get("/engine/status", response_model=DashboardSummary)
def get_engine_status(flight_id: int = Query(None, description="Flight to treat as the 'current' engine snapshot")):
    fid = flight_id if flight_id is not None else _pick_default_flight_id()
    if fid is None:
        return DashboardSummary(data_source="NGAFID historical telemetry", unavailable_parameters=KNOWN_UNAVAILABLE_PARAMETERS)
    return _build_dashboard(fid)


@router.get("/dashboard/summary", response_model=DashboardSummary)
def get_dashboard_summary(flight_id: int = Query(None, description="Flight to summarise; defaults to the demo flight")):
    fid = flight_id if flight_id is not None else _pick_default_flight_id()
    if fid is None:
        return DashboardSummary(data_source="NGAFID historical telemetry", unavailable_parameters=KNOWN_UNAVAILABLE_PARAMETERS)
    return _build_dashboard(fid)
