"""
app/services/rul_service.py
=============================
Prototype / illustrative Remaining-Useful-Life (RUL) estimation.

*** READ THIS BEFORE DEMOING RUL NUMBERS AS FACT ***

NGAFID gives us per-flight fault CLASSIFICATION labels, not continuous
run-to-failure degradation curves with a real "flights/hours until
failure" target. That means we cannot train a proper RUL regression
model here without more data. This module is explicit about that
limitation (see `requirements_for_production_model` in the response)
rather than pretending otherwise.

What we DO have, honestly:
  - `number_flights_before` in flight_header.csv, which (per the
    dataset schema given in the project brief) records how many
    flights an aircraft/engine had accumulated before a labelled
    event. We use it to compute a genuinely data-derived statistic:
    "historically, flights labelled X occurred after an average of N
    prior flights" - grouped straight from the real header data.
  - The prototype health_score for the flight in question.

We combine these into a single illustrative heuristic number, clearly
labelled LOW confidence, so the frontend has something to show, and
the report explains exactly how it was produced.
"""

from __future__ import annotations

import logging
from typing import Optional

import pandas as pd

from app.services import fault_prediction_service, health_index_service
from app.services.data_service import data_service

logger = logging.getLogger(__name__)

_stats_cache: Optional[pd.DataFrame] = None

REQUIREMENTS_FOR_PRODUCTION_RUL = [
    "Continuous run-to-failure sensor logs per airframe/engine (not just isolated labelled flights)",
    "A true remaining-time-or-flights-to-failure target for supervised regression",
    "Consistent engine/airframe identifiers across flights to build per-unit degradation histories",
    "Higher-rate vibration and wear-debris (oil analysis) data, which NGAFID does not include",
]


def _label_column(header: pd.DataFrame) -> Optional[str]:
    for candidate in ("label", "target_class", "hclass"):
        if candidate in header.columns:
            return candidate
    return None


def _historical_flights_before_stats(force_reload: bool = False) -> pd.DataFrame:
    """Group real flight_header.csv rows by fault label and compute the mean/
    median number_flights_before, dropping missing values. Cached in memory."""
    global _stats_cache
    if _stats_cache is not None and not force_reload:
        return _stats_cache

    header = data_service.load_header()
    label_col = _label_column(header)
    if label_col is None or "number_flights_before" not in header.columns:
        _stats_cache = pd.DataFrame()
        return _stats_cache

    valid = header.dropna(subset=["number_flights_before"])
    grouped = (
        valid.groupby(label_col)["number_flights_before"]
        .agg(["mean", "median", "count"])
        .reset_index()
        .rename(columns={label_col: "label"})
    )
    _stats_cache = grouped
    return grouped


def estimate_rul(flight_id: int) -> dict:
    health = health_index_service.compute_health_for_flight(flight_id)
    fault = fault_prediction_service.predict_for_flight(flight_id)

    fault_type = fault.get("fault_type")
    historical_baseline = None
    historical_sample_size = 0

    stats_df = _historical_flights_before_stats()
    if not stats_df.empty and fault_type:
        match = stats_df[stats_df["label"] == fault_type]
        if not match.empty:
            historical_baseline = float(match.iloc[0]["mean"])
            historical_sample_size = int(match.iloc[0]["count"])

    estimated_remaining_flights = None
    basis = (
        "No historical baseline available for this predicted fault type "
        "(either no fault was predicted, or too few labelled examples exist "
        "in flight_header.csv's number_flights_before column)."
    )
    if historical_baseline is not None:
        # Very rough heuristic: scale the historical "flights until this fault
        # type was recorded" by how healthy this flight currently looks.
        # This is NOT a trained regression - it is a documented illustrative
        # scaling, so it never claims more precision than it has.
        estimated_remaining_flights = round(historical_baseline * (health["health_score"] / 100.0), 1)
        basis = (
            f"Based on {historical_sample_size} historically labelled '{fault_type}' flights in "
            f"flight_header.csv, the average was {historical_baseline:.1f} prior flights before "
            f"the event was recorded. Scaled by this flight's current health score "
            f"({health['health_score']}/100) as an illustrative heuristic."
        )

    return {
        "flight_id": flight_id,
        "health_score": health["health_score"],
        "health_status": health["health_status"],
        "predicted_fault_type": fault_type,
        "estimated_remaining_flights": estimated_remaining_flights,
        "confidence": "LOW - prototype heuristic, not a trained RUL regression model",
        "basis": basis,
        "requirements_for_production_model": REQUIREMENTS_FOR_PRODUCTION_RUL,
        "is_prototype": True,
    }
