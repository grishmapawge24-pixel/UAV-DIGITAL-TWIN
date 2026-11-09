"""Replay-window analysis and model transparency endpoints."""
from fastapi import APIRouter, Query

from app.config import settings
from app.services.analysis_service import analyze_flight_window
from app.utils.errors import handle_service_errors

router = APIRouter(tags=["analysis"])


@router.get("/analyze/{flight_id}")
def analyze(flight_id: int, end_index: int | None = Query(None, ge=0), window: int = Query(120, ge=20, le=2000)):
    """Analyze a trailing window from actual historical telemetry for replay."""
    with handle_service_errors():
        return analyze_flight_window(flight_id, end_index, window)


@router.get("/reliability/{flight_id}")
def reliability(flight_id: int, end_index: int | None = Query(None, ge=0), window: int = Query(120, ge=20, le=2000)):
    with handle_service_errors():
        result = analyze_flight_window(flight_id, end_index, window)
    return {key: result[key] for key in ("flight_id", "window", "mission_reliability_index", "risk_level", "sensor_quality", "reliability_note")}


@router.get("/model/status")
def model_status():
    """Expose saved evaluation information so the UI cannot overstate model quality."""
    import json
    metrics = {}
    if settings.METRICS_PATH.exists():
        metrics = json.loads(settings.METRICS_PATH.read_text(encoding="utf-8"))
    return {"metrics": metrics, "note": "Use fault predictions only as prototype decision support; inspect macro-F1 and class-level metrics before relying on a class."}
