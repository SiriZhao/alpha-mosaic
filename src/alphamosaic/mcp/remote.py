"""Opt-in authenticated Streamable HTTP wrapper; no public deployment is performed."""

import os
import time
from collections import defaultdict, deque
from typing import Any

from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from alphamosaic.mcp.server import create_server


class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: Any, token: str, requests_per_minute: int = 60) -> None:
        super().__init__(app)
        self.token = token
        self.requests_per_minute = requests_per_minute
        self.hits: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request, call_next):  # type: ignore[no-untyped-def]
        if request.url.path == "/health":
            return await call_next(request)
        supplied = request.headers.get("authorization", "")
        if supplied != f"Bearer {self.token}":
            return JSONResponse({"status": "BLOCKED", "diagnostics": ["authentication required"]}, status_code=401)
        key = request.client.host if request.client else "unknown"
        now = time.monotonic()
        hits = self.hits[key]
        while hits and hits[0] <= now - 60:
            hits.popleft()
        if len(hits) >= self.requests_per_minute:
            return JSONResponse({"status": "DEGRADED", "diagnostics": ["rate limit exceeded"]}, status_code=429)
        hits.append(now)
        return await call_next(request)


def create_remote_app(token: str | None = None, requests_per_minute: int = 60) -> Starlette:
    bearer = token or os.environ.get("ALPHAMOSAIC_MCP_TOKEN")
    if not bearer or len(bearer) < 16:
        raise ValueError("ALPHAMOSAIC_MCP_TOKEN must be supplied and at least 16 characters")
    server = create_server()
    mcp_app = server.streamable_http_app(
        streamable_http_path="/", stateless_http=False, max_request_body_size=4 * 1024 * 1024,
        session_idle_timeout=1800, max_sessions=100,
    )

    async def health(_request):  # type: ignore[no-untyped-def]
        return JSONResponse({"status": "READY", "service": "AlphaMosaic MCP", "authenticated": True})

    app = Starlette(routes=[Route("/health", health), Mount("/mcp", app=mcp_app)])
    app.add_middleware(SecurityMiddleware, token=bearer, requests_per_minute=requests_per_minute)
    return app


def main() -> None:
    import uvicorn

    app = create_remote_app()
    uvicorn.run(app, host=os.environ.get("ALPHAMOSAIC_MCP_HOST", "127.0.0.1"), port=int(os.environ.get("ALPHAMOSAIC_MCP_PORT", "8000")))


if __name__ == "__main__":
    main()
