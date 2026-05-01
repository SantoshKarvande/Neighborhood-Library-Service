"""
app/proto_gen/serializer.py  (v2 – fixed)

Key fix vs v1:
    FastAPI route handlers return FLAT dicts that match Pydantic response
    schemas directly.  For example:

        POST /api/v1/authors  →  {"author_id": 1, "name": "Orwell"}

    But the proto message AuthorResponse wraps that in a field:
        message AuthorResponse { Author author = 1; }

    v1 tried to ParseDict the flat dict into AuthorResponse and got a
    DecodeError because the fields didn't match.

    v2 fixes this with a ROUTE_MAP that stores:
        (method, pattern, request_class, response_class, wrap_key)

    where `wrap_key` is the proto field name to wrap the flat FastAPI
    dict into before calling ParseDict.
    e.g.  wrap_key="author"  →  {"author": <flat_dict>}

    For endpoints that already return a dict matching the top-level
    proto message (like LibraryStats or paginated list envelopes),
    wrap_key=None and the dict is used as-is.
"""

from __future__ import annotations

import inspect
import re
from datetime import datetime, timezone
from typing import Any

from google.protobuf import json_format
from google.protobuf.message import Message

# Import generated stubs — run:  bash scripts/compile_proto.sh
from app.proto_gen import library_pb2 as pb


# ─── Route map ────────────────────────────────────────────────────────────────
#
# Each entry: (method, path_regex, request_cls, response_cls, wrap_key)
#
#   wrap_key : str  → wrap the FastAPI flat dict under this proto field name
#            : None → dict matches the top-level proto message directly
#
# FastAPI response shapes (from Pydantic schemas):
#   • Single objects (Author, Book, Member, BookCopy, Fine, BorrowTransaction)
#     are returned as flat dicts → need wrapping into the proto envelope.
#   • Paginated envelopes {"total":N,"items":[...]} are returned as dicts
#     → proto message fields are total + repeated field → need remapping.
#   • List endpoints (fines, copies) return bare Python lists.
#   • Stat/count dicts match proto fields directly → wrap_key=None.

ROUTE_MAP: list[tuple[str, str, type[Message] | None, type[Message] | None, str | None]] = [

    # ── Authors ───────────────────────────────────────────────────────────────
    ("GET",    r"^/api/v1/authors/?$",
        None,                    pb.AuthorListResponse,    None),          # paginated envelope
    ("POST",   r"^/api/v1/authors/?$",
        pb.CreateAuthorRequest,  pb.AuthorResponse,        "author"),
    ("GET",    r"^/api/v1/authors/\d+$",
        None,                    pb.AuthorResponse,        "author"),
    ("PATCH",  r"^/api/v1/authors/\d+$",
        pb.UpdateAuthorRequest,  pb.AuthorResponse,        "author"),
    ("DELETE", r"^/api/v1/authors/\d+$",
        None,                    None,                     None),

    # ── Books ─────────────────────────────────────────────────────────────────
    ("GET",    r"^/api/v1/books/?$",
        None,                    pb.BookListResponse,      None),
    ("POST",   r"^/api/v1/books/?$",
        pb.CreateBookRequest,    pb.BookResponse,          "book"),
    ("GET",    r"^/api/v1/books/\d+$",
        None,                    pb.BookResponse,          "book"),
    ("PATCH",  r"^/api/v1/books/\d+$",
        pb.UpdateBookRequest,    pb.BookResponse,          "book"),
    ("DELETE", r"^/api/v1/books/\d+$",
        None,                    None,                     None),
    ("GET",    r"^/api/v1/books/\d+/copies$",
        None,                    pb.CopyListResponse,      None),          # bare list
    ("POST",   r"^/api/v1/books/\d+/copies$",
        None,                    pb.BookResponse,          "book"),
    ("PATCH",  r"^/api/v1/books/copies/\d+/status$",
        None,                    pb.BookCopyResponse,      "copy"),

    # ── Members ───────────────────────────────────────────────────────────────
    ("GET",    r"^/api/v1/members/?$",
        None,                    pb.MemberListResponse,    None),
    ("POST",   r"^/api/v1/members/?$",
        pb.CreateMemberRequest,  pb.MemberResponse,        "member"),
    ("GET",    r"^/api/v1/members/\d+$",
        None,                    pb.MemberResponse,        "member"),
    ("PATCH",  r"^/api/v1/members/\d+$",
        pb.UpdateMemberRequest,  pb.MemberResponse,        "member"),
    ("DELETE", r"^/api/v1/members/\d+$",
        None,                    None,                     None),

    # ── Loans ─────────────────────────────────────────────────────────────────
    # Note: /stats and named paths MUST come before /\d+ patterns
    ("GET",    r"^/api/v1/loans/stats$",
        None,                    pb.LibraryStats,          None),          # flat dict matches proto
    ("GET",    r"^/api/v1/loans/borrowed$",
        None,                    pb.TransactionListResponse, None),
    ("GET",    r"^/api/v1/loans/due$",
        None,                    pb.TransactionListResponse, None),
    ("POST",   r"^/api/v1/loans/mark-overdue$",
        None,                    pb.MarkOverdueResponse,   None),
    ("POST",   r"^/api/v1/loans/fines/pay$",
        pb.PayFinesRequest,      pb.FineListResponse,      None),          # bare list
    ("GET",    r"^/api/v1/loans/?$",
        None,                    pb.TransactionListResponse, None),
    ("POST",   r"^/api/v1/loans/?$",
        pb.BorrowRequest,        pb.TransactionResponse,   "transaction"),
    ("GET",    r"^/api/v1/loans/\d+$",
        None,                    pb.TransactionResponse,   "transaction"),
    ("POST",   r"^/api/v1/loans/\d+/return$",
        pb.ReturnRequest,        pb.TransactionResponse,   "transaction"),
    ("GET",    r"^/api/v1/loans/\d+/fines$",
        None,                    pb.FineListResponse,      None),          # bare list
    ("GET",    r"^/api/v1/loans/members/\d+/fines$",
        None,                    pb.FineListResponse,      None),
]


def _find_entry(path: str, method: str):
    for m, pattern, req_cls, resp_cls, wrap_key in ROUTE_MAP:
        if m == method.upper() and re.match(pattern, path):
            return req_cls, resp_cls, wrap_key
    return None, None, None


# ─── Response: dict/list → Protobuf bytes ─────────────────────────────────────

def dict_to_proto_bytes(data: Any, path: str, method: str) -> bytes:
    """
    Convert a FastAPI JSON response (dict or list) to Protobuf binary.
    Raises ValueError if the route is not in ROUTE_MAP.
    """
    _, resp_cls, wrap_key = _find_entry(path, method)
    if resp_cls is None:
        raise ValueError(f"No response Protobuf class for {method} {path}")

    proto_dict = _shape_response(data, resp_cls, wrap_key)
    cleaned    = _prepare_for_proto(proto_dict)
    msg        = json_format.ParseDict(cleaned, resp_cls(), ignore_unknown_fields=True)
    return msg.SerializeToString()


def _shape_response(data: Any, resp_cls: type[Message], wrap_key: str | None) -> dict:
    """
    Transform the FastAPI response into a dict that matches the proto
    message field layout.
    """
    # ── Bare list (e.g. GET /fines, GET /copies) ──────────────────────────────
    if isinstance(data, list):
        return _wrap_bare_list(data, resp_cls)

    # ── Paginated envelope {"total":N, "skip":N, "limit":N, "items":[...]} ────
    if isinstance(data, dict) and "items" in data:
        return _remap_paginated(data, resp_cls)

    # ── Single object – wrap under the proto field name ───────────────────────
    if wrap_key is not None and isinstance(data, dict):
        return {wrap_key: data}

    # ── Dict matches proto top-level directly (stats, mark-overdue, etc.) ─────
    return data


def _wrap_bare_list(items: list, resp_cls: type[Message]) -> dict:
    """Map a bare list to the correct repeated field in the proto message."""
    name = resp_cls.DESCRIPTOR.name
    mapping = {
        "FineListResponse":        "fines",
        "CopyListResponse":        "copies",
        "AuthorListResponse":      "authors",
        "BookListResponse":        "books",
        "MemberListResponse":      "members",
        "TransactionListResponse": "transactions",
    }
    field = mapping.get(name)
    if field:
        return {field: items}
    # Fallback: put under first repeated field
    for fd in resp_cls.DESCRIPTOR.fields:
        if fd.label == fd.LABEL_REPEATED:
            return {fd.name: items}
    return {}


def _remap_paginated(data: dict, resp_cls: type[Message]) -> dict:
    """
    FastAPI paginated response:
        {"total": N, "skip": N, "limit": N, "items": [...]}

    Proto paginated message has:
        int32 total = 1;
        repeated <T> <field_name> = 2;

    This remaps "items" → the actual repeated field name.
    """
    items = data.get("items", [])
    result = {"total": data.get("total", len(items))}

    # Find the repeated field in the proto message
    for fd in resp_cls.DESCRIPTOR.fields:
        if fd.label == fd.LABEL_REPEATED:
            result[fd.name] = items
            break

    return result


# ─── Request: Protobuf bytes → dict ──────────────────────────────────────────

def proto_bytes_to_dict(raw: bytes, path: str, method: str) -> dict:
    """
    Parse an incoming Protobuf binary request body into a plain Python dict
    suitable for Pydantic / FastAPI to validate.
    """
    req_cls, _, _ = _find_entry(path, method)
    if req_cls is None:
        raise ValueError(f"No request Protobuf class for {method} {path}")

    msg = req_cls()
    msg.ParseFromString(raw)
    return _message_to_dict(msg)


def _message_to_dict(msg: Message) -> dict[str, Any]:
    """
    Convert a protobuf message to a dict across protobuf runtime versions.

    protobuf<5 uses `including_default_value_fields`, while protobuf>=5
    renamed that behavior to `always_print_fields_with_no_presence`.
    """
    kwargs: dict[str, Any] = {"preserving_proto_field_name": True}
    params = inspect.signature(json_format.MessageToDict).parameters

    if "always_print_fields_with_no_presence" in params:
        kwargs["always_print_fields_with_no_presence"] = True
    elif "including_default_value_fields" in params:
        kwargs["including_default_value_fields"] = True

    return json_format.MessageToDict(msg, **kwargs)


# ─── Protobuf JSON pre-processing ─────────────────────────────────────────────

def _prepare_for_proto(obj: Any) -> Any:
    """
    Recursively normalize FastAPI/Pydantic JSON values into the shape that
    protobuf json_format.ParseDict expects.

    - google.protobuf.Timestamp fields need RFC3339 strings with a timezone.
    - Python enum values like "AVAILABLE" need their protobuf enum names,
      e.g. "BOOK_STATUS_AVAILABLE".
    """
    if isinstance(obj, dict):
        normalized = {k: _prepare_for_proto(v) for k, v in obj.items()}
        _normalize_status_field(normalized)
        return normalized
    if isinstance(obj, list):
        return [_prepare_for_proto(i) for i in obj]
    if isinstance(obj, str):
        if _is_datetime(obj):
            return _timestamp_string(obj)
    return obj


def _normalize_status_field(data: dict[str, Any]) -> None:
    """Map API status strings to the correct generated protobuf enum names."""
    status = data.get("status")
    if not isinstance(status, str):
        return

    if "copy_id" in data and "member_id" not in data:
        data["status"] = f"BOOK_STATUS_{status}"
        return

    if "transaction_id" in data or "due_date" in data or "borrow_date" in data:
        data["status"] = f"TRANSACTION_STATUS_{status}"


def _timestamp_string(value: str) -> str:
    """
    Convert an ISO datetime string to protobuf JSON timestamp format.

    json_format.ParseDict expects Timestamp values as RFC3339 strings. FastAPI
    commonly emits naive datetimes without a trailing timezone, so normalize
    those to UTC with a trailing "Z".
    """
    s = value.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return value

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)

    return dt.isoformat().replace("+00:00", "Z")


def _is_datetime(s: str) -> bool:
    """Heuristic: string looks like an ISO datetime."""
    if len(s) < 19 or "T" not in s:
        return False

    try:
        datetime.fromisoformat(s.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False
