import json
import logging
import os
import sys
from datetime import datetime, timezone

from app.core.trace_context import request_id_var


class JSONFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
            "request_id": request_id_var.get(),
        }

        for key in (
            "document_id",
            "stage",
            "duration_ms",
            "chunk_count",
            "candidate_count",
            "scores",
            "status",
            "error_type",
            "model",
        ):
            if hasattr(record, key):
                payload[key] = getattr(record, key)

        if record.exc_info:
            payload["error_type"] = record.exc_info[0].__name__

        return json.dumps(payload, default=str)


def configure_logging():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    logger = logging.getLogger("chatbot")
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(
        os.getenv("LOG_LEVEL", "INFO").upper()
    )
    logger.propagate = False

    return logger
