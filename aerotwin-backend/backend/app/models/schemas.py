"""
app/models/schemas.py
=======================
Pydantic models describing every request/response body used by the API.

Keeping these in one file makes it easy to see the whole API "contract"
at a glance - useful when you're wiring up the React frontend and need
to know exactly what JSON shape to expect.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ============================================================================
# SHARED / SYSTEM
# ============================================================================

class HealthCheckResponse(BaseModel):
    status: str = Field(..., description="'ok' if the API process is up")
    app_name: str
    dataset_configured: bool
    dataset_path_exists: bool
    flight_header_loaded: bool
    sensor_mapping_available: bool
    sensor_mapping_verified: bool
    anomaly_model_loaded: bool
    fault_model_loaded: bool
    total_flights: Optional[int] = None
    message: str


class SensorAvailability(BaseModel):
    parameter: str
    group: Optional[str] = None
    available: bool
    source_column_index: Optional[int] = None


class SensorsAvailableResponse(BaseModel):
    mapping_verified: bool
    available_sensors: List[SensorAvailability]
    unavailable_sensors: List[str] = Field(
        default_factory=list,
        description="Parameters requested by the SIH problem statement that NGAFID "
                    "does not provide (e.g. Vibration, Injection Timing). Never fabricated.",
    )
    note: str


# ============================================================================
# FLIGHTS
# ============================================================================

class FlightSummary(BaseModel):
    flight_id: int
    label: Optional[Any] = None
    target_class: Optional[Any] = None
    hclass: Optional[Any] = None
    flight_length: Optional[float] = None
    before_after: Optional[Any] = None
    date_diff: Optional[float] = None
    number_flights_before: Optional[float] = None


class FlightListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    flights: List[FlightSummary]


class FlightDetail(FlightSummary):
    hierarchy: Optional[Any] = None
    fold: Optional[Any] = None
    engine_class: Optional[Any] = Field(None, alias="class")
    telemetry_available: bool
    num_timesteps: Optional[int] = None

    class Config:
        populate_by_name = True


class TelemetryPoint(BaseModel):
    timestep: float
    values: Dict[str, Optional[float]]


class TelemetryResponse(BaseModel):
    flight_id: int
    parameters: List[str]
    num_points: int
    downsampled: bool
    points: List[TelemetryPoint]
    data_source: str = "NGAFID historical telemetry"


class FlightHealthResponse(BaseModel):
    flight_id: int
    health_score: int
    health_status: str
    anomaly_detected: bool
    anomaly_score: Optional[float] = None
    contributing_factors: List[str]
    is_prototype: bool = True
    note: str


class FlightRulResponse(BaseModel):
    flight_id: int
    health_score: int
    health_status: str
    predicted_fault_type: Optional[str] = None
    estimated_remaining_flights: Optional[float] = None
    confidence: str
    basis: str
    requirements_for_production_model: List[str]
    is_prototype: bool = True


class FlightFaultsResponse(BaseModel):
    flight_id: int
    actual_label: Optional[str] = Field(
        None, description="Ground-truth label from flight_header.csv, if this flight is a labelled example"
    )
    fault_detected: bool
    fault_type: Optional[str] = None
    confidence: Optional[float] = None
    severity: Optional[str] = None
    recommended_action: Optional[str] = None
    uav_component: Optional[str] = None
    alert: bool = False
    model_status: Optional[str] = None
    candidate_fault_type: Optional[str] = None
    candidate_confidence: Optional[float] = None
    validation_note: Optional[str] = None


# ============================================================================
# PREDICTIONS (POST /api/predict, POST /api/anomaly)
# ============================================================================

class PredictRequest(BaseModel):
    flight_id: Optional[int] = Field(
        None, description="If given, features are computed from this flight's stored telemetry."
    )
    features: Optional[Dict[str, float]] = Field(
        None, description="Optional pre-computed feature vector, if you're not using flight_id."
    )


class PredictResponse(BaseModel):
    fault_detected: bool
    fault_type: Optional[str] = None
    confidence: Optional[float] = None
    severity: Optional[str] = None
    recommended_action: Optional[str] = None
    uav_component: Optional[str] = None
    alert: bool = False
    model_status: str
    candidate_fault_type: Optional[str] = None
    candidate_confidence: Optional[float] = None
    validation_note: Optional[str] = None


class AnomalyRequest(BaseModel):
    flight_id: Optional[int] = None
    features: Optional[Dict[str, float]] = None


class AnomalyResponse(BaseModel):
    anomaly_detected: bool
    anomaly_score: Optional[float] = None
    threshold: Optional[float] = None
    model_status: str


# ============================================================================
# MANUAL PARAMETER COMPARISON (POST /api/manual/evaluate)
# ============================================================================

class ManualParametersRequest(BaseModel):
    """All fields optional and in NGAFID-native units (RPM, degrees F for
    CHT/EGT/OilT, psi for OilP, gal/hr for fuel flow, volts for battery).
    Convert from display units (e.g. Celsius, bar, L/h) client-side before
    calling this endpoint. Anything left blank is assumed to be at the
    training-set average for that parameter."""
    rpm: Optional[float] = Field(None, description="Engine RPM")
    cht: Optional[float] = Field(None, description="Cylinder Head Temp, deg F (applied to all 4 cylinders)")
    egt: Optional[float] = Field(None, description="Exhaust Gas Temp, deg F (applied to all 4 cylinders)")
    oil_pressure: Optional[float] = Field(None, description="Oil pressure, psi")
    oil_temperature: Optional[float] = Field(None, description="Oil temperature, deg F")
    fuel_flow: Optional[float] = Field(None, description="Fuel flow, gal/hr")
    battery_voltage: Optional[float] = Field(None, description="Battery/bus voltage, volts (applied to volt1 & volt2)")
    advanced_parameters: Optional[Dict[str, float]] = Field(
        None,
        description="Power-user escape hatch: exact SENSOR_PARAMETERS names "
                    "(e.g. 'E1 CHT2', 'amp1', 'AltMSL') to set individual channels "
                    "the simple fields above don't cover. Overrides the simple fields "
                    "for that specific channel.",
    )


class ParameterComparison(BaseModel):
    parameter: str
    value: float
    baseline_mean: Optional[float] = None
    baseline_std: Optional[float] = None
    deviation_sigma: Optional[float] = None
    status: str = Field(..., description="'normal' | 'warning' | 'major' | 'critical' | 'offline' (no baseline yet)")
    direction: Optional[str] = Field(None, description="'high' | 'low' | null")


class ManualEvaluationResponse(BaseModel):
    parameters_provided: List[str]
    parameter_comparison: List[ParameterComparison]
    health_score: int
    health_status: str
    anomaly_detected: bool
    anomaly_score: Optional[float] = None
    fault_detected: bool
    fault_type: Optional[str] = None
    confidence: Optional[float] = None
    severity: Optional[str] = None
    recommended_action: Optional[str] = None
    uav_component: Optional[str] = None
    alert: bool = False
    model_status: str
    note: str


# ============================================================================
# MISSIONS
# ============================================================================

class MissionTemplate(BaseModel):
    flight_id: int
    label: Optional[str] = None
    flight_length: Optional[float] = None
    hclass: Optional[str] = None


class MissionListResponse(BaseModel):
    stored_missions: List[Dict[str, Any]]
    template_flights: List[MissionTemplate]
    note: str


class MissionSimulateRequest(BaseModel):
    base_flight_id: int = Field(..., description="Existing NGAFID flight to use as the mission profile")
    name: Optional[str] = Field(None, description="Optional label for this simulated mission")
    duration_scale: float = Field(
        1.0, ge=0.1, le=5.0,
        description="Scale the base flight's duration to simulate a longer/shorter mission (1.0 = unchanged)",
    )
    stress_factor: float = Field(
        1.0, ge=0.5, le=3.0,
        description="Multiplies engine load-related channels (RPM, EGT, CHT, FFlow) "
                    "to simulate a more/less demanding mission profile.",
    )


class MissionStep(BaseModel):
    checkpoint: float = Field(..., description="Fraction of the mission complete, 0.0 - 1.0")
    predicted_health_score: int
    predicted_status: str


class MissionSimulateResponse(BaseModel):
    mission_id: int
    base_flight_id: int
    name: Optional[str] = None
    params: Dict[str, float]
    predicted_trajectory: List[MissionStep]
    overall_risk: str
    fault_prediction: PredictResponse
    is_prototype: bool = True
    note: str


# ============================================================================
# REPLAY
# ============================================================================

class ReplayResponse(BaseModel):
    flight_id: int
    label: str = "Historical Telemetry Replay"
    parameters: List[str]
    num_points: int
    interval_ms: int
    points: List[TelemetryPoint]
    note: str = "This is replayed historical NGAFID telemetry, not live UAV data."


# ============================================================================
# DASHBOARD
# ============================================================================

class DashboardSummary(BaseModel):
    flight_id: Optional[int] = None
    engine_health: Optional[int] = None
    status: Optional[str] = None
    rpm: Optional[float] = None
    cht: Optional[float] = None
    egt: Optional[float] = None
    oil_pressure: Optional[float] = None
    oil_temperature: Optional[float] = None
    fuel_flow: Optional[float] = None
    battery_voltage: Optional[float] = None
    anomaly_detected: Optional[bool] = None
    fault_detected: Optional[bool] = None
    fault_type: Optional[str] = None
    confidence: Optional[float] = None
    maintenance_recommendation: Optional[str] = None
    data_source: str = "NGAFID historical telemetry"
    unavailable_parameters: List[str] = Field(default_factory=list)
