"""
app/config.py
==============
Central configuration for the AeroTwin AI backend.

Everything the backend needs to know about *where things live on disk*
and *how it should behave* is read from environment variables here, so
that the rest of the code never hard-codes a path.

Why this matters for you (student note):
-----------------------------------------
The raw NGAFID dataset (flight_header.csv, flight_data.pkl, stats.csv)
is several GB and lives on YOUR laptop, outside this backend folder.
You tell the backend where to find it by setting NGAFID_DATA_PATH in a
`.env` file (copy `.env.example` -> `.env` and edit it).

Nothing in this file talks to the dataset directly - it just resolves
paths and simple settings that other modules import.
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load variables from a .env file in the backend/ root, if present.
# (python-dotenv silently does nothing if the file doesn't exist, so
# this is safe to call even before the user has set anything up.)
BASE_DIR = Path(__file__).resolve().parent.parent  # .../backend
load_dotenv(BASE_DIR / ".env")


def _get_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


def _get_int(name: str, default: int) -> int:
    val = os.getenv(name)
    if val is None or val.strip() == "":
        return default
    try:
        return int(val)
    except ValueError:
        return default


class Settings:
    # ------------------------------------------------------------------
    # RAW DATASET LOCATION (lives OUTSIDE this repo, on your laptop)
    # ------------------------------------------------------------------
    # Example (Windows):  NGAFID_DATA_PATH=C:/Users/you/Datasets/ngafid
    # The folder is expected to directly contain:
    #   flight_header.csv, flight_data.pkl, stats.csv
    NGAFID_DATA_PATH: str = os.getenv("NGAFID_DATA_PATH", "")

    FLIGHT_HEADER_FILENAME: str = os.getenv("FLIGHT_HEADER_FILENAME", "flight_header.csv")
    FLIGHT_DATA_FILENAME: str = os.getenv("FLIGHT_DATA_FILENAME", "flight_data.pkl")
    STATS_FILENAME: str = os.getenv("STATS_FILENAME", "stats.csv")

    @property
    def flight_header_path(self) -> Path:
        return Path(self.NGAFID_DATA_PATH) / self.FLIGHT_HEADER_FILENAME

    @property
    def flight_data_pkl_path(self) -> Path:
        return Path(self.NGAFID_DATA_PATH) / self.FLIGHT_DATA_FILENAME

    @property
    def stats_csv_path(self) -> Path:
        return Path(self.NGAFID_DATA_PATH) / self.STATS_FILENAME

    # ------------------------------------------------------------------
    # LOCAL WORKING DIRECTORIES (live INSIDE this repo - small, derived files only)
    # ------------------------------------------------------------------
    DATA_DIR: Path = BASE_DIR / "data"
    PROCESSED_DIR: Path = DATA_DIR / "processed"           # per-flight .npy cache
    FEATURES_DIR: Path = DATA_DIR / "features"              # engineered feature tables
    CONFIG_DIR: Path = DATA_DIR / "config"                   # sensor_mapping.json lives here
    SQLITE_PATH: Path = DATA_DIR / "aerotwin.db"

    MODELS_DIR: Path = BASE_DIR / "models"
    ANOMALY_MODEL_PATH: Path = MODELS_DIR / "anomaly_model.pkl"
    FAULT_MODEL_PATH: Path = MODELS_DIR / "fault_model.pkl"
    SCALER_PATH: Path = MODELS_DIR / "scaler.pkl"
    LABEL_ENCODER_PATH: Path = MODELS_DIR / "label_encoder.pkl"
    FEATURE_COLUMNS_PATH: Path = MODELS_DIR / "feature_columns.json"
    METRICS_PATH: Path = MODELS_DIR / "metrics.json"

    SENSOR_MAPPING_PATH: Path = CONFIG_DIR / "sensor_mapping.json"

    # ------------------------------------------------------------------
    # APP BEHAVIOUR
    # ------------------------------------------------------------------
    APP_NAME: str = "AeroTwin AI Backend"
    API_PREFIX: str = "/api"

    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = _get_int("PORT", 8000)
    RELOAD: bool = _get_bool("RELOAD", True)
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Comma separated list of allowed frontend origins for CORS.
    # Covers the default ports used by Create React App (3000) and Vite (5173/4173).
    CORS_ORIGINS: list = [
        o.strip()
        for o in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000,"
            "http://localhost:5173,http://127.0.0.1:5173,"
            "http://localhost:4173,http://127.0.0.1:4173",
        ).split(",")
        if o.strip()
    ]

    # Health index thresholds (documented as prototype - see health_index_service.py)
    HEALTH_THRESHOLD_WARNING: int = _get_int("HEALTH_THRESHOLD_WARNING", 75)
    HEALTH_THRESHOLD_CRITICAL: int = _get_int("HEALTH_THRESHOLD_CRITICAL", 40)

    # Replay / streaming
    REPLAY_MAX_POINTS: int = _get_int("REPLAY_MAX_POINTS", 500)          # downsample cap for REST replay
    WS_DEFAULT_INTERVAL_MS: int = _get_int("WS_DEFAULT_INTERVAL_MS", 100)  # ms between streamed points

    # There is no live UAV connected to this backend - /api/engine/status and
    # /api/dashboard/summary need SOME flight to show by default when the
    # frontend doesn't pass ?flight_id=. Set this to pin a specific flight
    # for your demo; leave blank to just use the first flight in the dataset.
    DEMO_FLIGHT_ID: Optional[int] = (
        int(os.getenv("DEMO_FLIGHT_ID")) if os.getenv("DEMO_FLIGHT_ID", "").strip() else None
    )

    def ensure_local_dirs(self) -> None:
        """Create the small local working directories if they don't exist yet.
        Never touches NGAFID_DATA_PATH (that's read-only, external, and huge)."""
        for d in (self.DATA_DIR, self.PROCESSED_DIR, self.FEATURES_DIR,
                  self.CONFIG_DIR, self.MODELS_DIR):
            d.mkdir(parents=True, exist_ok=True)

    def dataset_configured(self) -> bool:
        """True if NGAFID_DATA_PATH is set and points at a real folder."""
        return bool(self.NGAFID_DATA_PATH) and Path(self.NGAFID_DATA_PATH).is_dir()


settings = Settings()
settings.ensure_local_dirs()
