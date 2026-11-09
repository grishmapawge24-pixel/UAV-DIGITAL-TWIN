"""
app/main.py
============
FastAPI application entrypoint for AeroTwin AI.

Run it with (from the backend/ folder, virtual env activated):

    uvicorn app.main:app --reload --port 8000

or just double-click / run `run_backend.bat` on Windows.

Then open:
    http://localhost:8000/           - basic status message
    http://localhost:8000/docs        - interactive Swagger UI (test every endpoint here)
"""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import (
    routes_faults,
    routes_flights,
    routes_health,
    routes_missions,
    routes_predictions,
    routes_replay,
    routes_analysis,
)
from app.config import settings
from app.services.data_service import DatasetNotConfiguredError, FlightNotFoundError
from app.services.preprocessing import MappingNotVerifiedError
from app.utils.db import init_db
from app.utils.logging_config import configure_logging

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Backend for AeroTwin AI - AI-Enabled Real-Time Digital Twin System for Health "
        "Monitoring, Fault Prediction and Mission Reliability Enhancement of Aero Piston "
        "Engines used in MALE UAVs (SIH 2026, Problem Statement 26054). "
        "All telemetry is real NGAFID historical flight data; nothing is simulated as fake sensor data."
    ),
    version="0.1.0",
)

# ---------------------------------------------------------------------------
# CORS - allows the React frontend (localhost:3000 for CRA, 5173/4173 for Vite
# by default) to call this API from the browser during local development.
# Edit CORS_ORIGINS in .env if your frontend runs on a different port.
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Clean JSON error responses for our own exception types, in case a route
# forgets to use `with handle_service_errors():`.
# ---------------------------------------------------------------------------
@app.exception_handler(DatasetNotConfiguredError)
async def dataset_not_configured_handler(request: Request, exc: DatasetNotConfiguredError):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.exception_handler(MappingNotVerifiedError)
async def mapping_not_verified_handler(request: Request, exc: MappingNotVerifiedError):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.exception_handler(FlightNotFoundError)
async def flight_not_found_handler(request: Request, exc: FlightNotFoundError):
    return JSONResponse(status_code=404, content={"detail": f"Flight {exc} not found"})


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(routes_health.router, prefix=settings.API_PREFIX)
app.include_router(routes_flights.router, prefix=settings.API_PREFIX)
app.include_router(routes_faults.router, prefix=settings.API_PREFIX)
app.include_router(routes_predictions.router, prefix=settings.API_PREFIX)
app.include_router(routes_missions.router, prefix=settings.API_PREFIX)
app.include_router(routes_replay.router, prefix=settings.API_PREFIX)
app.include_router(routes_analysis.router, prefix=settings.API_PREFIX)

# The WebSocket lives at /ws/telemetry/{flight_id} - no /api prefix, as
# specified in the project brief - so it's mounted separately, at the root.
app.include_router(routes_replay.ws_router)


@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "status": "running",
        "docs": "/docs",
        "api_prefix": settings.API_PREFIX,
        "websocket": "/ws/telemetry/{flight_id}",
    }


@app.on_event("startup")
def on_startup():
    init_db()
    if not settings.dataset_configured():
        logger.warning(
            "NGAFID_DATA_PATH is not set/valid (currently '%s'). The API will start, but "
            "data-dependent endpoints will return HTTP 503 until you set it in .env and restart. "
            "See SETUP_GUIDE.md.",
            settings.NGAFID_DATA_PATH,
        )
    else:
        logger.info("NGAFID_DATA_PATH = %s", settings.NGAFID_DATA_PATH)
    logger.info("%s ready. Visit http://%s:%s/docs to explore the API.",
                settings.APP_NAME, "localhost", settings.PORT)
