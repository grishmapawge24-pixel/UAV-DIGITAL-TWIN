"""
app/services/data_service.py
==============================
The ONLY module that touches the raw NGAFID files directly:

    flight_header.csv   - small, one row per flight, loaded eagerly & cached
    stats.csv            - small, per-parameter statistics, loaded eagerly & cached
    flight_data.pkl       - ~2.7GB dict[flight_id] -> np.ndarray (T, 23) float16

Why a dedicated "data service" instead of reading files all over the app?
---------------------------------------------------------------------------
1. flight_data.pkl is huge. We do NOT want to unpickle the whole 2.7GB
   dict on every request. This module caches it in memory after the
   first access, and - much better - prefers a pre-processed per-flight
   cache (data/processed/flights/<id>.npy) built once by
   `ml/preprocess_dataset.py`, so a single flight can be loaded in
   milliseconds without touching the other 11,445 flights at all.

2. Every route/service asks THIS module for data, so there is exactly
   one place that needs to know about file paths, dtypes, and the raw
   dataset's quirks.

3. If NGAFID_DATA_PATH isn't configured yet, everything here fails
   gracefully with clear, catchable errors instead of crashing FastAPI
   at import time - so you can still explore /docs and the parts of the
   API that don't need data.
"""

from __future__ import annotations

import logging
import pickle
import threading
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from app.config import settings

logger = logging.getLogger(__name__)


class DatasetNotConfiguredError(RuntimeError):
    """NGAFID_DATA_PATH is not set or does not point at a real folder."""


class FlightNotFoundError(KeyError):
    """The requested flight_id does not exist in flight_header.csv / flight_data.pkl."""


class DataService:
    def __init__(self):
        self._header_df: Optional[pd.DataFrame] = None
        self._stats_df: Optional[pd.DataFrame] = None
        self._pkl_cache: Optional[Dict[int, np.ndarray]] = None
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Availability
    # ------------------------------------------------------------------
    def dataset_configured(self) -> bool:
        return settings.dataset_configured()

    def _require_dataset(self) -> None:
        if not self.dataset_configured():
            raise DatasetNotConfiguredError(
                f"NGAFID_DATA_PATH is not set to a valid folder (currently: "
                f"'{settings.NGAFID_DATA_PATH}'). Copy .env.example to .env and set "
                f"NGAFID_DATA_PATH to the folder containing flight_header.csv, "
                f"flight_data.pkl and stats.csv."
            )

    # ------------------------------------------------------------------
    # flight_header.csv
    # ------------------------------------------------------------------
    def load_header(self, force_reload: bool = False) -> pd.DataFrame:
        if self._header_df is not None and not force_reload:
            return self._header_df
        self._require_dataset()
        path = settings.flight_header_path
        if not path.exists():
            raise FileNotFoundError(f"flight_header.csv not found at {path}")
        logger.info("Loading flight_header.csv from %s", path)
        df = pd.read_csv(path)

        # Normalise the index column name so the rest of the app can rely on
        # a column literally called "Master Index" (matches the brief) while
        # also exposing a lowercase alias `flight_id` used throughout our API.
        if "Master Index" in df.columns:
            df["flight_id"] = df["Master Index"]
        elif "flight_id" not in df.columns:
            # Last resort: use the row position. Logged loudly because this
            # would mean the CSV doesn't match the documented schema.
            logger.warning(
                "flight_header.csv has no 'Master Index' column - falling back "
                "to row position as flight_id. Please check the file schema."
            )
            df["flight_id"] = df.index

        df["flight_id"] = df["flight_id"].astype(int)
        df = df.set_index("flight_id", drop=False)
        self._header_df = df
        return df

    def header_row(self, flight_id: int) -> pd.Series:
        df = self.load_header()
        if flight_id not in df.index:
            raise FlightNotFoundError(flight_id)
        return df.loc[flight_id]

    def flight_ids(self) -> List[int]:
        return self.load_header().index.tolist()

    # ------------------------------------------------------------------
    # stats.csv
    # ------------------------------------------------------------------
    def load_stats(self, force_reload: bool = False) -> pd.DataFrame:
        if self._stats_df is not None and not force_reload:
            return self._stats_df
        self._require_dataset()
        path = settings.stats_csv_path
        if not path.exists():
            raise FileNotFoundError(f"stats.csv not found at {path}")
        logger.info("Loading stats.csv from %s", path)
        self._stats_df = pd.read_csv(path)
        return self._stats_df

    # ------------------------------------------------------------------
    # flight_data.pkl / per-flight processed cache
    # ------------------------------------------------------------------
    def _processed_path(self, flight_id: int) -> Path:
        return settings.PROCESSED_DIR / "flights" / f"{flight_id}.npy"

    def has_processed_cache(self, flight_id: int) -> bool:
        return self._processed_path(flight_id).exists()

    def _load_full_pkl(self) -> Dict[int, np.ndarray]:
        """Loads the ENTIRE 2.7GB flight_data.pkl into memory. Slow. Cached
        after first call. Prefer the per-flight processed cache instead -
        see ml/preprocess_dataset.py."""
        with self._lock:
            if self._pkl_cache is not None:
                return self._pkl_cache
            self._require_dataset()
            path = settings.flight_data_pkl_path
            if not path.exists():
                raise FileNotFoundError(f"flight_data.pkl not found at {path}")
            logger.warning(
                "Loading the FULL flight_data.pkl (~2.7GB) into memory. This can "
                "take a while and use a lot of RAM. Run "
                "`python ml/preprocess_dataset.py` once to build a fast per-flight "
                "cache and avoid this in future."
            )
            with open(path, "rb") as f:
                data = pickle.load(f)
            logger.info("flight_data.pkl loaded: %d flights in memory", len(data))
            self._pkl_cache = data
            return data

    def get_flight_array(self, flight_id: int) -> np.ndarray:
        """Returns the raw (T, 23) float32 array for one flight - unmapped
        column indices, i.e. exactly the columns as they exist in
        flight_data.pkl. Use app.utils.sensor_mapping to interpret columns."""
        processed = self._processed_path(flight_id)
        if processed.exists():
            arr = np.load(processed)
        else:
            # Cheap early-exit: if flight_header.csv doesn't know this flight_id
            # at all, don't pay the cost of loading the entire ~2.7GB pickle
            # just to discover that. (Only helps once the header is loaded,
            # which every route already does anyway.)
            try:
                if flight_id not in self.load_header().index:
                    raise FlightNotFoundError(flight_id)
            except (DatasetNotConfiguredError, FileNotFoundError):
                pass  # fall through - let the pkl-loading path below raise the real error

            data = self._load_full_pkl()
            if flight_id not in data:
                raise FlightNotFoundError(flight_id)
            arr = data[flight_id]

        # float16 is fine for storage but risky for arithmetic (overflow,
        # precision loss in slopes/rolling stats) - upcast for computation.
        return np.asarray(arr, dtype=np.float32)

    def flight_data_available(self, flight_id: int) -> bool:
        if self.has_processed_cache(flight_id):
            return True
        if not self.dataset_configured():
            return False
        try:
            data = self._load_full_pkl()
        except (FileNotFoundError, DatasetNotConfiguredError):
            return False
        return flight_id in data


# Module-level singleton
data_service = DataService()
