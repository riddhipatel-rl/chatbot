import logging
import time
from contextlib import contextmanager

logger = logging.getLogger("chatbot.tracing")


@contextmanager
def trace_stage(stage, **metadata):
    start = time.perf_counter()

    try:
        yield metadata

    except Exception as exc:
        duration_ms = round(
            (time.perf_counter() - start) * 1000,
            2,
        )

        logger.exception(
            "pipeline_stage_failed",
            extra={
                "stage": stage,
                "duration_ms": duration_ms,
                "status": "failed",
                "error_type": type(exc).__name__,
                **metadata,
            },
        )
        raise

    else:
        duration_ms = round(
            (time.perf_counter() - start) * 1000,
            2,
        )

        logger.info(
            "pipeline_stage_completed",
            extra={
                "stage": stage,
                "duration_ms": duration_ms,
                "status": "success",
                **metadata,
            },
        )
