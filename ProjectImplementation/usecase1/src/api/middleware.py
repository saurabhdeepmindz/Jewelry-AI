"""FastAPI middleware stack.

TraceIDMiddleware — injected on every request:
  - Reads X-Trace-ID from incoming headers (or generates a UUID4)
  - Sets trace_id_var context variable so all logs within the request include it
  - Returns X-Trace-ID in every response header for client-side correlation
"""
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.logging import get_logger, trace_id_var

logger = get_logger(__name__)


class TraceIDMiddleware(BaseHTTPMiddleware):
    """Propagates X-Trace-ID through the full request lifecycle."""

    async def dispatch(self, request: Request, call_next: object) -> Response:
        trace_id = request.headers.get("X-Trace-ID") or str(uuid.uuid4())
        token = trace_id_var.set(trace_id)
        request.state.trace_id = trace_id

        try:
            response: Response = await call_next(request)  # type: ignore[operator]
        finally:
            trace_id_var.reset(token)

        response.headers["X-Trace-ID"] = trace_id
        return response
