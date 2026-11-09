"""
app/utils/sensor_mapping.py
=============================
This module is the SINGLE source of truth for how the 23 raw numeric
columns inside each `flight_data[flight_id]` NumPy array (shape ~
(n_timesteps, 23), dtype float16) correspond to named sensor
parameters such as "E1 RPM" or "E1 OilP".

WHY THIS FILE EXISTS
---------------------
The project brief is explicit: we must NOT assume or invent this
mapping. `stats.csv` lists the named parameters, and `flight_data.pkl`
has 23 unnamed numeric columns per flight - but nothing in the raw
dataset directly says "column 0 = volt1, column 1 = volt2, ...".

So the real mapping is produced by `ml/verify_sensor_mapping.py`,
which statistically compares each pkl column against the per-parameter
statistics in stats.csv and writes its best-guess mapping (with a
confidence score) to `data/config/sensor_mapping.json`.

THIS FILE NEVER GUESSES. It only:
  1. Knows the canonical list of parameter names that *should* exist
     (taken straight from the project brief / stats.csv column list).
  2. Loads whatever mapping verify_sensor_mapping.py has produced.
  3. Tells the rest of the app whether that mapping has been marked
     VERIFIED by a human, and refuses to silently treat an
     unverified/auto-suggested mapping as ground truth.

If you (the student) haven't run the verification script yet, every
function below will clearly say so instead of crashing or making
something up.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Optional

from app.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Canonical parameter names, exactly as they appear in stats.csv.
# `timestep` and `cluster` are metadata columns, not engine sensor channels,
# so we track them separately from the 23 "real" sensor channels.
# ---------------------------------------------------------------------------
SENSOR_PARAMETERS = [
    "volt1", "volt2", "amp1", "amp2",
    "FQtyL", "FQtyR",
    "E1 FFlow", "E1 OilT", "E1 OilP", "E1 RPM",
    "E1 CHT1", "E1 CHT2", "E1 CHT3", "E1 CHT4",
    "E1 EGT1", "E1 EGT2", "E1 EGT3", "E1 EGT4",
    "OAT", "IAS", "VSpd", "NormAc", "AltMSL",
]
METADATA_PARAMETERS = ["timestep", "cluster"]
ALL_STATS_PARAMETERS = SENSOR_PARAMETERS + METADATA_PARAMETERS

# Human-friendly grouping, used by health-index / dashboard logic so that
# e.g. "give me all 4 cylinder head temps" doesn't need to be hard-coded
# everywhere. Purely a convenience layer on top of SENSOR_PARAMETERS.
PARAMETER_GROUPS = {
    "battery": ["volt1", "volt2", "amp1", "amp2"],
    "fuel_quantity": ["FQtyL", "FQtyR"],
    "fuel_flow": ["E1 FFlow"],
    "oil": ["E1 OilT", "E1 OilP"],
    "rpm": ["E1 RPM"],
    "cht": ["E1 CHT1", "E1 CHT2", "E1 CHT3", "E1 CHT4"],
    "egt": ["E1 EGT1", "E1 EGT2", "E1 EGT3", "E1 EGT4"],
    "environment": ["OAT", "IAS", "VSpd", "NormAc", "AltMSL"],
}

# Parameters requested by the SIH problem statement that NGAFID does NOT
# provide. The API must clearly mark these as unavailable rather than
# fabricate values - see routes_health.py -> /api/sensors/available.
KNOWN_UNAVAILABLE_PARAMETERS = ["Vibration", "Injection Timing"]


class SensorMapping:
    """Loads and exposes the verified pkl-column -> parameter-name mapping."""

    def __init__(self, path: Path = settings.SENSOR_MAPPING_PATH):
        self.path = path
        self._raw: Optional[dict] = None
        self._index_to_name: Dict[int, str] = {}
        self._name_to_index: Dict[str, int] = {}
        self._verified = False
        self._load()

    # -- loading ------------------------------------------------------
    def _load(self) -> None:
        if not self.path.exists():
            logger.warning(
                "Sensor mapping file not found at %s. "
                "Run `python ml/verify_sensor_mapping.py` first. "
                "Endpoints that need real telemetry will report 'mapping not verified' "
                "until this is done.",
                self.path,
            )
            return

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                self._raw = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Could not read sensor mapping file %s: %s", self.path, exc)
            return

        self._verified = bool(self._raw.get("verified", False))
        mapping = self._raw.get("mapping", {})
        # JSON keys are strings; column indices should be ints.
        for k, v in mapping.items():
            try:
                idx = int(k)
            except ValueError:
                continue
            name = v.get("parameter") if isinstance(v, dict) else v
            if name:
                self._index_to_name[idx] = name
                self._name_to_index[name] = idx

        if not self._verified:
            logger.warning(
                "Sensor mapping at %s exists but is NOT marked verified=true. "
                "It is an auto-suggested mapping from verify_sensor_mapping.py. "
                "Open the file, visually sanity-check the suggested column<->parameter "
                "pairing against the printed value ranges, then set \"verified\": true "
                "yourself before trusting it for training or the live API.",
                self.path,
            )

    def reload(self) -> None:
        self._raw = None
        self._index_to_name = {}
        self._name_to_index = {}
        self._verified = False
        self._load()

    # -- public API -----------------------------------------------------
    @property
    def is_available(self) -> bool:
        """A mapping file exists and was successfully parsed (may still be unverified)."""
        return self._raw is not None

    @property
    def is_verified(self) -> bool:
        """A human has opened data/config/sensor_mapping.json and set verified: true."""
        return self._verified

    @property
    def usable(self) -> bool:
        """Safe to use for real inference / training."""
        return self.is_available and self.is_verified

    def get_name_for_index(self, index: int) -> Optional[str]:
        return self._index_to_name.get(index)

    def get_index_for_name(self, name: str) -> Optional[int]:
        return self._name_to_index.get(name)

    def mapped_parameters(self) -> list:
        """Which of the canonical SENSOR_PARAMETERS currently have a column mapped."""
        return [p for p in SENSOR_PARAMETERS if p in self._name_to_index]

    def missing_parameters(self) -> list:
        return [p for p in SENSOR_PARAMETERS if p not in self._name_to_index]

    def as_dict(self) -> dict:
        return {
            "mapping_file": str(self.path),
            "available": self.is_available,
            "verified": self.is_verified,
            "mapped_count": len(self._index_to_name),
            "expected_count": len(SENSOR_PARAMETERS),
            "index_to_name": dict(sorted(self._index_to_name.items())),
            "missing_parameters": self.missing_parameters(),
            "unavailable_by_dataset": KNOWN_UNAVAILABLE_PARAMETERS,
        }


# Module-level singleton, imported everywhere as `from app.utils.sensor_mapping import sensor_mapping`
sensor_mapping = SensorMapping()
