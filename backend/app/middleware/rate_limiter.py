"""
Rate Limiter Middleware for GeoShield API.

The limiter is intentionally lightweight and in-memory because GeoShield is a
single-process research/demo prototype. A production-scale deployment should
move rate-limit state to a shared store such as Redis.
"""
import os
import time
from collections import defaultdict
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class RateLimiter(BaseHTTPMiddleware):
    """
    In-memory per-client rate limiter.

    Defaults:
    - 100 requests/minute for normal API traffic
    - 10 requests/minute for authentication

    X-Forwarded-For is ignored unless TRUST_PROXY_HEADERS=true. This prevents a
    direct client from spoofing the header to bypass limits.
    """

    def __init__(
        self,
        app,
        general_limit: int = 100,
        auth_limit: int = 10,
        window_seconds: int = 60,
    ):
        super().__init__(app)
        self.general_limit = general_limit
        self.auth_limit = auth_limit
        self.window_seconds = window_seconds
        self.trust_proxy_headers = _env_bool("TRUST_PROXY_HEADERS", False)
        self.requests: dict[str, list[float]] = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        if self.trust_proxy_headers:
            forwarded = request.headers.get("X-Forwarded-For")
            if forwarded:
                return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _is_rate_limited(self, client_ip: str, path: str) -> bool:
        now = time.time()
        cutoff = now - self.window_seconds
        auth_request = "/auth/" in path
        limit = self.auth_limit if auth_request else self.general_limit
        key = f"{client_ip}:{'auth' if auth_request else 'general'}"

        self.requests[key] = [timestamp for timestamp in self.requests[key] if timestamp > cutoff]
        if len(self.requests[key]) >= limit:
            return True

        self.requests[key].append(now)
        return False

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Health/static/non-API routes do not consume the API rate budget.
        if path in {"/health", "/api/health"} or not path.startswith("/api/"):
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        if self._is_rate_limited(client_ip, path):
            return Response(
                content='{"detail":"Rate limit exceeded. Try again later."}',
                status_code=429,
                media_type="application/json",
                headers={"Retry-After": str(self.window_seconds)},
            )

        return await call_next(request)
