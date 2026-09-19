"""Small, dependency-free production observability primitives."""

from __future__ import annotations

import json
import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware


class JsonLogFormatter(logging.Formatter):
    """Emit machine-readable logs while keeping request URLs query-free."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%SZ"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "event"):
            payload["event"] = record.event
        return json.dumps(payload, ensure_ascii=False)


def configure_structured_logging() -> None:
    logger = logging.getLogger("tenderpulse.request")
    if logger.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(JsonLogFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Attach a request id and emit a single privacy-conscious access event."""

    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            logging.getLogger("tenderpulse.request").exception(
                "request_failed",
                extra={"event": {"request_id": request_id, "method": request.method, "path": request.url.path}},
            )
            raise

        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        logging.getLogger("tenderpulse.request").info(
            "request_complete",
            extra={"event": {"request_id": request_id, "method": request.method, "path": request.url.path, "status": response.status_code, "duration_ms": duration_ms}},
        )
        return response
