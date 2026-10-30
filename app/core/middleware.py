
import logging
import time
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware

from app.core.trace_context import request_id_var

logger = logging.getLogger("chatbot.api")


class RequestTracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = str(uuid4())
        token = request_id_var.set(request_id)
        start = time.perf_counter()

        try:
            response = await call_next(request)

            duration_ms = round(
                (time.perf_counter() - start) * 1000,
                2,
            )

            response.headers["X-Request-ID"] = request_id

            logger.info(
                "http_request_completed",
                extra={
                    "stage": "http",
                    "duration_ms": duration_ms,
                    "status": response.status_code,
                },
            )

            return response

        except Exception:
            logger.exception(
                "http_request_failed",
                extra={
                    "stage": "http",
                    "duration_ms": round(
                        (time.perf_counter() - start) * 1000,
                        2,
                    ),
                    "status": "failed",
                },
            )
            raise

        finally:
            request_id_var.reset(token)
