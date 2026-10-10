"""Opt-in authenticated Streamable HTTP wrapper; no public deployment is performed."""

import json
import os
import time
from collections import defaultdict, deque
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.routing import Route

from alphamosaic.mcp.server import create_server


class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: Any,
        token: str,
        requests_per_minute: int = 60,
        max_body_bytes: int = 4 * 1024 * 1024,
        allow_insecure_localhost: bool = True,
    ) -> None:
        super().__init__(app)
        self.token = token
        self.requests_per_minute = requests_per_minute
        self.max_body_bytes = max_body_bytes
        self.allow_insecure_localhost = allow_insecure_localhost
        self.hits: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request, call_next):  # type: ignore[no-untyped-def]
        if request.url.path == "/health":
            return await call_next(request)
        host = (request.url.hostname or "").lower()
        local = host in {"localhost", "127.0.0.1", "::1"}
        forwarded_proto = request.headers.get("x-forwarded-proto", request.url.scheme).lower()
        if not (local and self.allow_insecure_localhost) and forwarded_proto != "https":
            return JSONResponse(
                {"status": "BLOCKED", "diagnostics": ["HTTPS is required for non-local MCP access"]},
                status_code=400,
            )
        content_length = request.headers.get("content-length")
        if content_length and content_length.isdigit() and int(content_length) > self.max_body_bytes:
            return JSONResponse(
                {"status": "BLOCKED", "diagnostics": ["request body exceeds configured limit"]},
                status_code=413,
            )
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
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response


class AuditMiddleware(BaseHTTPMiddleware):
    """Write redacted request metadata without recording credentials or payloads."""

    def __init__(self, app: Any, path: Path | None = None) -> None:
        super().__init__(app)
        self.path = path

    async def dispatch(self, request, call_next):  # type: ignore[no-untyped-def]
        response = await call_next(request)
        if self.path is not None:
            record = {
                "at": datetime.now(UTC).isoformat(),
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "client": request.client.host if request.client else None,
            }
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, separators=(",", ":")) + "\n")
        return response


def create_remote_app(
    token: str | None = None,
    requests_per_minute: int = 60,
    audit_path: Path | None = None,
    allow_insecure_localhost: bool = True,
) -> Starlette:
    bearer = token or os.environ.get("ALPHAMOSAIC_MCP_TOKEN")
    if not bearer or len(bearer) < 16:
        raise ValueError("ALPHAMOSAIC_MCP_TOKEN must be supplied and at least 16 characters")
    server = create_server()
    mcp_app = server.streamable_http_app(
        streamable_http_path="/mcp", stateless_http=False, max_request_body_size=4 * 1024 * 1024,
        session_idle_timeout=1800, max_sessions=100,
    )

    async def health(_request):  # type: ignore[no-untyped-def]
        return JSONResponse({"status": "READY", "service": "AlphaMosaic MCP", "authenticated": True})

    # Add health to the MCP-owned app so its lifespan starts and session state is retained.
    mcp_app.routes.insert(0, Route("/health", health))
    audit = audit_path
    if audit is None and os.environ.get("ALPHAMOSAIC_AUDIT_LOG"):
        audit = Path(os.environ["ALPHAMOSAIC_AUDIT_LOG"]).expanduser()
    mcp_app.add_middleware(
        SecurityMiddleware,
        token=bearer,
        requests_per_minute=requests_per_minute,
        allow_insecure_localhost=allow_insecure_localhost,
    )
    mcp_app.add_middleware(AuditMiddleware, path=audit)
    return mcp_app


def main() -> None:
    import uvicorn

    app = create_remote_app()
    uvicorn.run(app, host=os.environ.get("ALPHAMOSAIC_MCP_HOST", "127.0.0.1"), port=int(os.environ.get("ALPHAMOSAIC_MCP_PORT", "8000")))


if __name__ == "__main__":
    main()
