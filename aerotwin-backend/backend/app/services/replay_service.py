"""
app/services/replay_service.py
================================
Serves a flight's telemetry back "as if" it were arriving in real time.

*** This is always historical NGAFID data being replayed - never live
UAV telemetry. Every response is labelled "Historical Telemetry Replay"
so the frontend (and anyone watching the demo) can't mistake it for a
live feed. ***

Two consumption modes:
  - REST (routes_replay.py -> GET /api/replay/{flight_id}): returns an
    optionally-downsampled batch of points in one response.
  - WebSocket (routes_replay.py -> /ws/telemetry/{flight_id}): an async
    generator that yields one point at a time with a configurable delay,
    for a live-feeling chart animation.
"""

from __future__ import annotations

import asyncio
import logging
from typing import AsyncIterator, Dict, List

import numpy as np
import pandas as pd

from app.config import settings
from app.services.data_service import data_service
from app.services.preprocessing import flight_array_to_clean_df
from app.utils.sensor_mapping import SENSOR_PARAMETERS

logger = logging.getLogger(__name__)


def downsample(df: pd.DataFrame, max_points: int) -> pd.DataFrame:
    if len(df) <= max_points:
        return df
    idx = np.linspace(0, len(df) - 1, max_points).astype(int)
    # Preserve source sample indices so a replay client can request analysis
    # for the same point in the original flight, rather than its position in
    # a downsampled display array.
    return df.iloc[idx]


def to_points(df: pd.DataFrame) -> List[Dict]:
    points = []
    for i, row in df.iterrows():
        values = {}
        for p in SENSOR_PARAMETERS:
            v = row.get(p)
            values[p] = None if v is None or (isinstance(v, float) and np.isnan(v)) else float(v)
        points.append({"timestep": float(i), "values": values})
    return points


def get_replay_batch(flight_id: int, max_points: int = None) -> dict:
    max_points = max_points or settings.REPLAY_MAX_POINTS
    raw = data_service.get_flight_array(flight_id)
    df = flight_array_to_clean_df(raw)
    total = len(df)
    downsampled_df = downsample(df, max_points)

    return {
        "flight_id": flight_id,
        "label": "Historical Telemetry Replay",
        "parameters": SENSOR_PARAMETERS,
        "num_points": len(downsampled_df),
        "interval_ms": settings.WS_DEFAULT_INTERVAL_MS,
        "points": to_points(downsampled_df),
        "note": (
            f"This is replayed historical NGAFID telemetry, not live UAV data. "
            f"{total} original timesteps downsampled to {len(downsampled_df)} points."
        ),
    }


async def stream_replay(flight_id: int, interval_ms: int = None, max_points: int = None) -> AsyncIterator[dict]:
    """Async generator: yields one telemetry point at a time, waiting
    `interval_ms` milliseconds between points, for the /ws/telemetry
    endpoint. Always historical data played back at a demo-friendly pace."""
    interval_ms = interval_ms or settings.WS_DEFAULT_INTERVAL_MS
    max_points = max_points or settings.REPLAY_MAX_POINTS

    raw = data_service.get_flight_array(flight_id)
    df = flight_array_to_clean_df(raw)
    downsampled_df = downsample(df, max_points)
    points = to_points(downsampled_df)

    for i, point in enumerate(points):
        yield {
            "flight_id": flight_id,
            "label": "Historical Telemetry Replay",
            "index": i,
            "total": len(points),
            "point": point,
        }
        await asyncio.sleep(interval_ms / 1000.0)
