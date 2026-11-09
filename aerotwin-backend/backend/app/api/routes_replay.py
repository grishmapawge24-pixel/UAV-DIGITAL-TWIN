"""
app/api/routes_replay.py
==========================
    GET /api/replay/{flight_id}     - one-shot batch of (downsampled) historical telemetry
    WS  /ws/telemetry/{flight_id}    - streamed, point-by-point historical telemetry

Both are always "Historical Telemetry Replay" - see replay_service.py.
"""

import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

from app.config import settings
from app.models.schemas import ReplayResponse
from app.services import replay_service
from app.services.data_service import DatasetNotConfiguredError, FlightNotFoundError
from app.services.preprocessing import MappingNotVerifiedError
from app.utils.errors import handle_service_errors

logger = logging.getLogger(__name__)

# Mounted under /api in main.py
router = APIRouter(tags=["replay"])

# Mounted at the root (no /api prefix) in main.py, since /ws/telemetry/{id}
# is the exact path requested in the project brief.
ws_router = APIRouter(tags=["replay-websocket"])


@router.get("/replay/{flight_id}", response_model=ReplayResponse)
def get_replay(
    flight_id: int,
    max_points: int = Query(None, description="Downsample cap; defaults to REPLAY_MAX_POINTS"),
):
    with handle_service_errors():
        result = replay_service.get_replay_batch(flight_id, max_points=max_points)
    return ReplayResponse(**result)


@ws_router.websocket("/ws/telemetry/{flight_id}")
async def ws_telemetry(
    websocket: WebSocket,
    flight_id: int,
    interval_ms: int = None,
    max_points: int = None,
):
    """Streams one telemetry point at a time, as if it were live. It is
    replayed historical NGAFID data - every message says so.

    Connect from the frontend with, e.g.:
        new WebSocket(`ws://localhost:8000/ws/telemetry/${flightId}?interval_ms=100`)
    """
    await websocket.accept()
    interval = interval_ms or settings.WS_DEFAULT_INTERVAL_MS
    try:
        async for message in replay_service.stream_replay(flight_id, interval_ms=interval, max_points=max_points):
            await websocket.send_json(message)
        await websocket.send_json({"event": "done", "flight_id": flight_id})
    except WebSocketDisconnect:
        logger.info("Client disconnected from /ws/telemetry/%s", flight_id)
    except (DatasetNotConfiguredError, MappingNotVerifiedError, FlightNotFoundError, FileNotFoundError) as exc:
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.send_json({"event": "error", "detail": str(exc)})
    finally:
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.close()
