"""
app/utils/errors.py
=====================
Maps our internal, specific exceptions to sensible HTTP responses, so
every route doesn't have to repeat the same try/except logic.

Usage in a route:

    from app.utils.errors import handle_service_errors

    @router.get("/flights/{flight_id}")
    def get_flight(flight_id: int):
        with handle_service_errors():
            ...
"""

from contextlib import contextmanager

from fastapi import HTTPException

from app.services.data_service import DatasetNotConfiguredError, FlightNotFoundError
from app.services.preprocessing import MappingNotVerifiedError


@contextmanager
def handle_service_errors():
    try:
        yield
    except DatasetNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except MappingNotVerifiedError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except FlightNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Flight {exc} not found") from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
