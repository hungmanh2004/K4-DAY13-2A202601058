from __future__ import annotations

import re
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from structlog.contextvars import bind_contextvars, clear_contextvars


CORRELATION_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def _correlation_id(value: str | None) -> str:
    if value and CORRELATION_ID_PATTERN.fullmatch(value):
        return value
    return f"req-{uuid.uuid4().hex[:8]}"


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        clear_contextvars()

        correlation_id = _correlation_id(request.headers.get("x-request-id"))

        bind_contextvars(correlation_id=correlation_id)

        request.state.correlation_id = correlation_id

        start = time.perf_counter()
        response = await call_next(request)

        response.headers["x-request-id"] = correlation_id
        response.headers["x-response-time-ms"] = str(int((time.perf_counter() - start) * 1000))

        return response
