"""
app/utils/logging_config.py
=============================
One place to set up Python logging for the whole backend.

Call `configure_logging()` once, at startup (main.py does this).
Everywhere else just do:

    import logging
    logger = logging.getLogger(__name__)
    logger.info("something happened")
"""

import logging
import sys

from app.config import settings


def configure_logging() -> None:
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    root = logging.getLogger()
    root.setLevel(level)

    # Avoid duplicate handlers if configure_logging() is called more than once
    # (e.g. under --reload, uvicorn re-imports the app).
    if root.handlers:
        return

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)

    # Quiet down some noisy third-party loggers so the demo terminal stays readable
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("watchfiles").setLevel(logging.WARNING)
