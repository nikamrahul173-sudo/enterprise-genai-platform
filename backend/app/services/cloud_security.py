import hmac
import os
import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class PublicDemoSecurityMiddleware(BaseHTTPMiddleware):
    """
    Public demo protection.

    This is lightweight, per-process protection, not a replacement
    for production authentication or distributed rate limiting.
    """

    def __init__(self, app):
        super().__init__(app)
        self.requests_by_ip = defaultdict(deque)
        self.global_requests = deque()

    async def dispatch(self, request, call_next):
        if os.getenv("PUBLIC_DEMO_MODE", "0") != "1":
            return await call_next(request)

        # Allow browser CORS preflight requests.
        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path
        method = request.method.upper()

        protected = (
            (method == "POST" and path == "/tickets")
            or (method == "POST" and path == "/tickets/analyze")
            or (
                method == "POST"
                and path.startswith("/tickets/")
            )
            or (
                method == "PATCH"
                and path.startswith("/tickets/")
            )
            or (
                method == "POST"
                and path == "/documents/upload"
            )
            or (
                method == "DELETE"
                and path.startswith("/documents/")
            )
        )

        if protected:
            expected = os.getenv("ADMIN_API_TOKEN", "")
            provided = request.headers.get("X-Admin-Token", "")

            if (
                not expected
                or not provided
                or not hmac.compare_digest(provided, expected)
            ):
                return JSONResponse(
                    {"detail": "Admin authorization required."},
                    status_code=403,
                )

        # Limit public AI requests to reduce accidental quota abuse.
        # The counters reset when the process restarts.
        ai_endpoint = (
            method == "POST"
            and path in {"/chat", "/rag/chat"}
        )

        if ai_endpoint:
            now = time.monotonic()
            ip = (
                request.client.host
                if request.client
                else "unknown"
            )

            recent = self.requests_by_ip[ip]

            while recent and now - recent[0] > 3600:
                recent.popleft()

            while (
                self.global_requests
                and now - self.global_requests[0] > 86400
            ):
                self.global_requests.popleft()

            if len(recent) >= 10:
                return JSONResponse(
                    {"detail": "Hourly AI demo limit reached."},
                    status_code=429,
                )

            if len(self.global_requests) >= 100:
                return JSONResponse(
                    {"detail": "Daily AI demo limit reached."},
                    status_code=429,
                )

            recent.append(now)
            self.global_requests.append(now)

        return await call_next(request)
