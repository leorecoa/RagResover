import logging
import re
import secrets
import time
from uuid import uuid4

from fastapi import Request, Response

from app.core.metrics import request_metrics


logger = logging.getLogger("rag_resover")
REQUEST_ID_HEADER = "X-Request-ID"
TRACEPARENT_HEADER = "traceparent"
TRACEPARENT_PATTERN = re.compile(
    r"^(?P<version>[0-9a-f]{2})-"
    r"(?P<trace_id>[0-9a-f]{32})-"
    r"(?P<span_id>[0-9a-f]{16})-"
    r"(?P<trace_flags>[0-9a-f]{2})$"
)


def build_trace_context(raw_traceparent: str | None) -> tuple[str, str, str, str]:
    if raw_traceparent:
        match = TRACEPARENT_PATTERN.fullmatch(raw_traceparent.strip().lower())
        if match and match.group("trace_id") != "0" * 32:
            return (
                match.group("version"),
                match.group("trace_id"),
                secrets.token_hex(8),
                match.group("trace_flags"),
            )

    return "00", uuid4().hex, secrets.token_hex(8), "01"


async def request_observability_middleware(request: Request, call_next) -> Response:
    request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid4())
    trace_version, trace_id, span_id, trace_flags = build_trace_context(
        request.headers.get(TRACEPARENT_HEADER)
    )
    started_at = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (time.perf_counter() - started_at) * 1000
        logger.exception(
            "request_failed",
            extra={
                "request_id": request_id,
                "trace_id": trace_id,
                "span_id": span_id,
                "method": request.method,
                "path": request.url.path,
                "duration_ms": round(duration_ms, 2),
            },
        )
        raise

    duration_ms = (time.perf_counter() - started_at) * 1000
    response.headers[REQUEST_ID_HEADER] = request_id
    response.headers[TRACEPARENT_HEADER] = (
        f"{trace_version}-{trace_id}-{span_id}-{trace_flags}"
    )
    route = request.scope.get("route")
    path = getattr(route, "path", request.url.path)
    request_metrics.record(
        method=request.method,
        path=path,
        status_code=response.status_code,
        duration_ms=duration_ms,
    )
    logger.info(
        "request_completed",
        extra={
            "request_id": request_id,
            "trace_id": trace_id,
            "span_id": span_id,
            "method": request.method,
            "path": path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
        },
    )
    return response
