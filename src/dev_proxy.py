"""Reverse proxy handler forwarding requests to the Vite development server."""

import httpx
from fastapi import Request, Response

_VITE_DEV_HOST: str = "localhost"
_VITE_DEV_PORT: int = 5173
_EXCLUDED_PROXY_HEADERS: frozenset[str] = frozenset(
    {"host", "content-encoding", "transfer-encoding", "content-length"}
)


async def _dev_proxy(request: Request) -> Response:
    """Proxy all non-API requests to the Vite dev server in development mode."""
    target_url = f"http://{_VITE_DEV_HOST}:{_VITE_DEV_PORT}{request.url.path}"
    if request.url.query:
        target_url = f"{target_url}?{request.url.query}"
    headers = {
        k: v
        for k, v in request.headers.items()
        if k.lower() not in _EXCLUDED_PROXY_HEADERS
    }
    async with httpx.AsyncClient() as client:
        proxy_response = await client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=await request.body(),
            follow_redirects=True,
        )
    response_headers = {
        k: v
        for k, v in proxy_response.headers.items()
        if k.lower() not in _EXCLUDED_PROXY_HEADERS
    }
    return Response(
        content=proxy_response.content,
        status_code=proxy_response.status_code,
        headers=response_headers,
    )
