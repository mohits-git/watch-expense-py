from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp


class APIGatewayProxyMiddleware:
    """
    Handle API Gateway proxy headers with trusted host validation

    Referenced from ProxyHeadersMiddleware source code in Uvicorn:
      - https://github.com/Kludex/uvicorn/blob/main/uvicorn/middleware/proxy_headers.py
    """

    def __init__(self, app: ASGIApp, trusted_hosts: str | list[str] = "*"):
        self.app = app
        self.always_trust = trusted_hosts == "*"

    async def __call__(self, scope, receive, send):
        if scope["type"] not in ("http", "websocket"):
            return await self.app(scope, receive, send)

        client_addr = scope.get("client")
        client_host = client_addr[0] if client_addr else None

        # Only process if from trusted source
        if self.always_trust or not client_host or client_host == "127.0.0.1":
            headers = dict(scope["headers"])

            # Handle proto
            if b"api-x-forwarded-proto" in headers:
                proto = headers[b"api-x-forwarded-proto"].decode(
                    "latin1").strip()
                if proto in {"http", "https", "ws", "wss"}:
                    scope["scheme"] = proto.replace(
                        "http", "ws") if scope["type"] == "websocket" else proto

            # Handle forwarded-for
            if b"api-x-forwarded-for" in headers:
                forwarded_for = headers[b"api-x-forwarded-for"].decode(
                    "latin1").strip()
                if forwarded_for:
                    # Get first IP (the original client)
                    host = forwarded_for.split(",")[0].strip()
                    if host:
                        scope["client"] = (host, 0)

        return await self.app(scope, receive, send)


def register_middlewares(app: FastAPI):
    app.add_middleware(APIGatewayProxyMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        allow_origins=[
            "https://watchexpense.mohits.me",
            "http://localhost:4200"
        ],
    )
