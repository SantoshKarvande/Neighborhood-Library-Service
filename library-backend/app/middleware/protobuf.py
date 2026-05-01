"""
app/middleware/protobuf.py  (v2 – fixed)

Root causes fixed vs v1:
  1. _PatchedRequest now properly overrides the ASGI `receive` callable
     (not just .body()) so FastAPI actually reads the injected JSON body.
  2. Response Protobuf class selection now accounts for the fact that
     FastAPI routes return FLAT dicts, not wrapped ones.
     e.g.  POST /authors  returns {"author_id":1,"name":"..."} directly,
     NOT   {"author": {"author_id":1,"name":"..."}}
  3. Error details are logged to stderr so you can diagnose issues without
     the middleware silently swallowing them.
"""

import json
import sys
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.proto_gen import library_pb2 as pb, serializer


class ProtobufMiddleware(BaseHTTPMiddleware):
    """
    Transparent JSON ↔ Protobuf content-negotiation middleware.

    Clients signal encoding via standard HTTP headers:
        Content-Type: application/x-protobuf   →  request body is binary Protobuf
        Accept:       application/x-protobuf   →  client wants a binary Protobuf response

    Omit both headers and the API behaves exactly as JSON (backward compatible).
    """

    PROTO_CT = "application/x-protobuf"

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # ── 1. Convert incoming Protobuf body → JSON so FastAPI can parse it ──
        content_type = request.headers.get("content-type", "")
        if self.PROTO_CT in content_type:
            raw_body = await request.body()
            if raw_body:
                try:
                    data_dict = serializer.proto_bytes_to_dict(
                        raw_body, request.url.path, request.method
                    )
                    json_bytes = json.dumps(data_dict).encode()
                    # Patch the original request in-place so downstream FastAPI
                    # reads JSON instead of the original protobuf bytes.
                    _patch_request_as_json(request, json_bytes)
                except Exception as exc:
                    print(f"[ProtobufMiddleware] request decode error: {exc}", file=sys.stderr)
                    return _error_response(
                        request,
                        status_code=400,
                        error="Bad Request",
                        detail=f"Protobuf request deserialization failed: {exc}",
                    )

        # ── 2. Call the actual route handler ──────────────────────────────────
        response = await call_next(request)

        # ── 3. Convert JSON response → Protobuf binary if client requested it ─
        accept = request.headers.get("accept", "")
        if self.PROTO_CT not in accept:
            return response

        # Drain the response body
        body_bytes = b""
        async for chunk in response.body_iterator:
            body_bytes += chunk

        # Non-2xx (e.g. 404, 422) — return the JSON error as-is so the
        # caller can read a meaningful message instead of garbage bytes.
        if response.status_code >= 400:
            return _error_response(
                request,
                status_code=response.status_code,
                error=_http_error_name(response.status_code),
                detail=_extract_error_detail(body_bytes),
                raw_json=body_bytes,
            )

        try:
            data = json.loads(body_bytes)
            proto_bytes = serializer.dict_to_proto_bytes(
                data, request.url.path, request.method
            )
            return Response(
                content=proto_bytes,
                status_code=response.status_code,
                media_type=self.PROTO_CT,
            )
        except Exception as exc:
            # Log and fall back to JSON so the caller is not left with silence
            print(f"[ProtobufMiddleware] response encode error: {exc}", file=sys.stderr)
            return Response(
                content=body_bytes,
                status_code=response.status_code,
                media_type="application/json",
                headers={"X-Proto-Error": str(exc)},
            )


# ─── Request body replacement ─────────────────────────────────────────────────

def _patch_request_as_json(request: Request, json_bytes: bytes) -> None:
    """
    Patch the existing Request so its body becomes `json_bytes` and its
    Content-Type header is switched to application/json.

    Patching in place is more reliable with BaseHTTPMiddleware than
    constructing a replacement Request object.
    """
    # Update scope headers so downstream parsing treats the body as JSON.
    new_headers = [
        (k, v)
        for k, v in request.scope.get("headers", [])
        if k.lower() not in (b"content-type", b"content-length")
    ]
    new_headers.append((b"content-type", b"application/json"))
    new_headers.append((b"content-length", str(len(json_bytes)).encode()))
    request.scope["headers"] = new_headers

    # Build an ASGI receive callable that returns our bytes on first call,
    # then an empty body on subsequent calls.
    _sent = False

    async def patched_receive():
        nonlocal _sent
        if not _sent:
            _sent = True
            return {"type": "http.request", "body": json_bytes, "more_body": False}
        return {"type": "http.request", "body": b"", "more_body": False}

    request._receive = patched_receive
    request._body = json_bytes


def _http_error_name(status_code: int) -> str:
    mapping = {
        400: "Bad Request",
        404: "Not Found",
        409: "Conflict",
        422: "Unprocessable Entity",
        500: "Internal Server Error",
    }
    return mapping.get(status_code, "Request Failed")


def _extract_error_detail(body_bytes: bytes) -> str:
    try:
        payload = json.loads(body_bytes)
    except Exception:
        return body_bytes.decode("utf-8", errors="replace")

    if isinstance(payload, dict):
        detail = payload.get("detail", payload)
        if isinstance(detail, (dict, list)):
            return json.dumps(detail)
        return str(detail)
    return str(payload)


def _error_response(
    request: Request,
    status_code: int,
    error: str,
    detail: str,
    raw_json: bytes | None = None,
) -> Response:
    if ProtobufMiddleware.PROTO_CT in request.headers.get("accept", ""):
        msg = pb.ErrorResponse(status_code=status_code, error=error, detail=detail)
        return Response(
            content=msg.SerializeToString(),
            status_code=status_code,
            media_type=ProtobufMiddleware.PROTO_CT,
        )

    if raw_json is not None:
        return Response(content=raw_json, status_code=status_code, media_type="application/json")

    return Response(
        content=json.dumps({"detail": detail}).encode(),
        status_code=status_code,
        media_type="application/json",
    )
