"""
app/api/routes_missions.py
============================
    GET /api/missions            - previously simulated missions + template flights to try
    POST /api/missions/simulate   - run a new what-if mission simulation
"""

import logging

from fastapi import APIRouter

from app.models.schemas import (
    MissionListResponse,
    MissionSimulateRequest,
    MissionSimulateResponse,
    MissionTemplate,
)
from app.services import mission_service
from app.services.data_service import data_service
from app.utils.db import list_missions
from app.utils.errors import handle_service_errors

logger = logging.getLogger(__name__)
router = APIRouter(tags=["missions"])


@router.get("/missions", response_model=MissionListResponse)
def get_missions(template_count: int = 10):
    stored = list_missions()

    templates = []
    with handle_service_errors():
        header = data_service.load_header()
    sample = header.head(template_count)
    for _, row in sample.iterrows():
        templates.append(
            MissionTemplate(
                flight_id=int(row.get("flight_id")),
                label=row.get("label") if isinstance(row.get("label"), str) else None,
                flight_length=row.get("flight_length"),
                hclass=row.get("hclass") if isinstance(row.get("hclass"), str) else None,
            )
        )

    return MissionListResponse(
        stored_missions=stored,
        template_flights=templates,
        note=(
            "template_flights are real NGAFID flights you can use as a mission "
            "'base_flight_id' in POST /api/missions/simulate. stored_missions are "
            "previously run simulations, saved locally in SQLite."
        ),
    )


@router.post("/missions/simulate", response_model=MissionSimulateResponse)
def simulate_mission(request: MissionSimulateRequest):
    with handle_service_errors():
        result = mission_service.simulate_mission(
            base_flight_id=request.base_flight_id,
            name=request.name,
            duration_scale=request.duration_scale,
            stress_factor=request.stress_factor,
        )
    return MissionSimulateResponse(**result)
