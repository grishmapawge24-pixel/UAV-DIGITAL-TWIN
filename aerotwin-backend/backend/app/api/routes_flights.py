"""
app/api/routes_flights.py
===========================
    GET /api/flights                         - paginated list of flights
    GET /api/flights/{flight_id}              - one flight's header info
    GET /api/flights/{flight_id}/telemetry    - mapped sensor readings
    GET /api/flights/{flight_id}/health        - prototype health score
"""

import math
from typing import Optional

import numpy as np
from fastapi import APIRouter, Query

from app.config import settings
from app.models.schemas import (
    FlightDetail,
    FlightHealthResponse,
    FlightListResponse,
    FlightRulResponse,
    FlightSummary,
    TelemetryResponse,
)
from app.services import health_index_service, rul_service
from app.services.data_service import data_service
from app.services.preprocessing import flight_array_to_clean_df
from app.services.replay_service import downsample, to_points
from app.utils.errors import handle_service_errors
from app.utils.sensor_mapping import SENSOR_PARAMETERS

router = APIRouter(tags=["flights"])


def _clean(v):
    if v is None:
        return None
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    if isinstance(v, (np.floating,)):
        return float(v)
    if isinstance(v, (np.integer,)):
        return int(v)
    return v


def _row_to_summary(row) -> FlightSummary:
    return FlightSummary(
        flight_id=int(row.get("flight_id")),
        label=_clean(row.get("label")),
        target_class=_clean(row.get("target_class")),
        hclass=_clean(row.get("hclass")),
        flight_length=_clean(row.get("flight_length")),
        before_after=_clean(row.get("before_after")),
        date_diff=_clean(row.get("date_diff")),
        number_flights_before=_clean(row.get("number_flights_before")),
    )


@router.get("/flights", response_model=FlightListResponse)
def list_flights(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=500),
    label: Optional[str] = Query(None, description="Case-insensitive substring filter on the fault label"),
):
    with handle_service_errors():
        header = data_service.load_header()

    df = header
    if label:
        label_cols = [c for c in ("label", "target_class") if c in df.columns]
        if label_cols:
            mask = False
            for c in label_cols:
                mask = mask | df[c].astype(str).str.contains(label, case=False, na=False)
            df = df[mask]

    total = len(df)
    start = (page - 1) * page_size
    end = start + page_size
    page_df = df.iloc[start:end]

    flights = [_row_to_summary(row) for _, row in page_df.iterrows()]
    return FlightListResponse(total=total, page=page, page_size=page_size, flights=flights)


@router.get("/flights/{flight_id}", response_model=FlightDetail)
def get_flight(flight_id: int):
    with handle_service_errors():
        row = data_service.header_row(flight_id)
        available = data_service.flight_data_available(flight_id)
        num_timesteps = None
        if available:
            try:
                arr = data_service.get_flight_array(flight_id)
                num_timesteps = int(arr.shape[0])
            except Exception:  # noqa: BLE001
                num_timesteps = None

    return FlightDetail(
        flight_id=int(row.get("flight_id")),
        label=_clean(row.get("label")),
        target_class=_clean(row.get("target_class")),
        hclass=_clean(row.get("hclass")),
        flight_length=_clean(row.get("flight_length")),
        before_after=_clean(row.get("before_after")),
        date_diff=_clean(row.get("date_diff")),
        number_flights_before=_clean(row.get("number_flights_before")),
        hierarchy=_clean(row.get("hierarchy")),
        fold=_clean(row.get("fold")),
        **{"class": _clean(row.get("class"))},
        telemetry_available=available,
        num_timesteps=num_timesteps,
    )


@router.get("/flights/{flight_id}/telemetry", response_model=TelemetryResponse)
def get_flight_telemetry(
    flight_id: int,
    max_points: int = Query(None, description="Downsample cap; defaults to REPLAY_MAX_POINTS"),
):
    max_points = max_points or settings.REPLAY_MAX_POINTS
    with handle_service_errors():
        raw = data_service.get_flight_array(flight_id)
        df = flight_array_to_clean_df(raw)

    total = len(df)
    downsampled = downsample(df, max_points)
    return TelemetryResponse(
        flight_id=flight_id,
        parameters=SENSOR_PARAMETERS,
        num_points=len(downsampled),
        downsampled=len(downsampled) < total,
        points=to_points(downsampled),
    )


@router.get("/flights/{flight_id}/health", response_model=FlightHealthResponse)
def get_flight_health(flight_id: int):
    with handle_service_errors():
        result = health_index_service.compute_health_for_flight(flight_id)
    return FlightHealthResponse(**result)


@router.get("/flights/{flight_id}/rul", response_model=FlightRulResponse)
def get_flight_rul(flight_id: int):
    """Prototype Remaining-Useful-Life estimate. Not in the brief's minimum
    endpoint list, but RUL estimation IS one of the required SIH features
    (see rul_service.py docstring for exactly what this is and isn't)."""
    with handle_service_errors():
        result = rul_service.estimate_rul(flight_id)
    return FlightRulResponse(**result)
