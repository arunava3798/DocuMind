"""Structured (JSON) logging configuration."""
from __future__ import annotations

import json
import logging
import sys

from ..config import get_settings

_configured = False


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        context = getattr(record, "ctx", None)
        if isinstance(context, dict):
            payload.update(context)
        return json.dumps(payload)


def configure_logging() -> None:
    global _configured
    if _configured:
        return
    settings = get_settings()
    handler = logging.StreamHandler(sys.stdout)
    if settings.log_json:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(levelname)s %(name)s %(message)s"))
    logger = logging.getLogger("rag")
    logger.handlers = [handler]
    logger.setLevel(settings.log_level)
    logger.propagate = False
    _configured = True


def get_logger() -> logging.Logger:
    configure_logging()
    return logging.getLogger("rag")
