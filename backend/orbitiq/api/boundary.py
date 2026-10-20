"""Bounded ingress and redacted request records; proxy limits remain necessary."""

import json
import logging
import re
import time
import uuid
from datetime import UTC, datetime

from starlette.responses import JSONResponse

from orbitiq.runtime import Settings

LOGGER = logging.getLogger("orbitiq.requests")
EXPENSIVE = re.compile(
    r"^/api/(?:comparisons|snapshots/[^/]+/(?:position|earth-fixed)|"
    r"satellites/[^/]+/ground-track)/?$"
)


class HTTPBoundary:
    def __init__(self, app, settings: Settings):
        self.app, self.settings = app, settings
        self.calculations = 0

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        request_id = uuid.uuid4().hex
        started = time.monotonic()
        status, size, response_started = 500, 0, False
        admitted = False

        async def respond(message):
            nonlocal status, size, response_started
            if message["type"] == "http.response.start":
                response_started = True
                status = message["status"]
                headers = message.setdefault("headers", [])
                headers.extend(
                    [
                        (b"x-request-id", request_id.encode()),
                        (b"x-content-type-options", b"nosniff"),
                        (b"x-frame-options", b"DENY"),
                        (b"referrer-policy", b"no-referrer"),
                    ]
                )
                if not any(k.lower() == b"cache-control" for k, _ in headers):
                    headers.append((b"cache-control", b"no-store"))
            elif message["type"] == "http.response.body":
                size += len(message.get("body", b""))
            await send(message)

        async def refuse(code, message, http_status, headers=None):
            await JSONResponse(
                {"detail": message, "error": {"code": code, "message": message}},
                status_code=http_status,
                headers=headers,
            )(scope, receive, respond)

        try:
            if self.settings.production:
                if (
                    len(scope.get("raw_path", b""))
                    + len(scope.get("query_string", b""))
                    > 4096
                ):
                    return await refuse(
                        "request_too_large", "Request URI too long", 414
                    )
                if sum(len(k) + len(v) for k, v in scope["headers"]) > 16384:
                    return await refuse(
                        "headers_too_large", "Request headers too large", 431
                    )
                if scope["method"] not in {"GET", "HEAD", "OPTIONS"}:
                    return await refuse(
                        "read_only", "This API is read-only", 405, {"Allow": "GET"}
                    )
                lengths = [v for k, v in scope["headers"] if k == b"content-length"]
                if any(v != b"0" for v in lengths) or any(
                    k == b"transfer-encoding" for k, _ in scope["headers"]
                ):
                    return await refuse(
                        "body_disallowed", "Read requests have no body", 413
                    )
                if EXPENSIVE.fullmatch(scope["path"]):
                    # No await between admission check/increment: one event loop,
                    # one worker as required by the release command.
                    if self.calculations >= self.settings.max_calculations:
                        return await refuse(
                            "capacity",
                            "Calculation capacity busy; retry later",
                            503,
                            {"Retry-After": "1"},
                        )
                    self.calculations += 1
                    admitted = True
            await self.app(scope, receive, respond)
        except Exception:
            if response_started:
                raise
            await refuse(
                "internal_error", "Request failed safely; retry or contact support", 500
            )
        finally:
            if admitted:
                self.calculations -= 1
            route = scope.get("route")
            method = scope["method"]
            LOGGER.info(
                json.dumps(
                    {
                        "event": "http_request",
                        "at_utc": datetime.now(UTC).isoformat(),
                        "request_id": request_id,
                        "method": method
                        if method
                        in {"GET", "HEAD", "OPTIONS", "POST", "PUT", "PATCH", "DELETE"}
                        else "OTHER",
                        "route": getattr(route, "path", "unmatched"),
                        "status": status,
                        "duration_ms": round((time.monotonic() - started) * 1000, 3),
                        "response_bytes": size,
                    },
                    separators=(",", ":"),
                )
            )
