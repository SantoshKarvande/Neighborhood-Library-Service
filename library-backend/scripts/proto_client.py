"""
scripts/proto_client.py

A demonstration client that communicates with the Library REST API
using Protocol Buffers instead of JSON.

Shows:
  - Sending Protobuf binary request bodies
  - Receiving and parsing Protobuf binary response bodies
  - Falling back to JSON where convenient

Usage:
    pip install requests protobuf grpcio-tools
    python scripts/compile_proto.sh        # generate stubs first
    python scripts/proto_client.py
"""

import sys
import os
from datetime import datetime, timedelta, timezone

# Allow imports from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import requests
from google.protobuf import json_format, timestamp_pb2
from google.protobuf.message import DecodeError

from app.proto_gen import library_pb2 as pb

BASE_URL = "http://localhost:8000/api/v1"

PROTO_HEADERS = {
    "Content-Type": "application/x-protobuf",
    "Accept":       "application/x-protobuf",
}
JSON_HEADERS = {
    "Content-Type": "application/json",
    "Accept":       "application/json",
}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def to_ts(dt: datetime) -> timestamp_pb2.Timestamp:
    ts = timestamp_pb2.Timestamp()
    ts.FromDatetime(dt.astimezone(timezone.utc).replace(tzinfo=None))
    return ts


def print_proto(label: str, msg: pb, status: int):
    print(f"\n{'='*60}")
    print(f"  {label}  [HTTP {status}]")
    print(f"{'='*60}")
    print(json_format.MessageToJson(msg, indent=2))


def print_section(title: str):
    print(f"\n{'#'*60}")
    print(f"  {title}")
    print(f"{'#'*60}")


def parse_proto_response(resp: requests.Response, success_msg, label: str):
    """
    Decode either the expected success protobuf or ErrorResponse and print JSON.
    """
    if "application/x-protobuf" not in resp.headers.get("content-type", ""):
        raise RuntimeError(
            f"{label} returned non-protobuf response "
            f"[HTTP {resp.status_code}]: {resp.text}"
        )

    if resp.status_code >= 400:
        err = pb.ErrorResponse()
        err.ParseFromString(resp.content)
        print_proto(f"{label} (Error)", err, resp.status_code)
        return None

    try:
        success_msg.ParseFromString(resp.content)
    except DecodeError as exc:
        raise RuntimeError(
            f"{label} returned invalid protobuf payload [HTTP {resp.status_code}]: {exc}"
        ) from exc

    print_proto(label, success_msg, resp.status_code)
    return success_msg


# ─── API calls ────────────────────────────────────────────────────────────────

def create_author_proto(name: str) -> pb.Author:
    """POST /authors — send and receive Protobuf."""
    req = pb.CreateAuthorRequest(name=name)
    resp = requests.post(
        f"{BASE_URL}/authors/",
        data=req.SerializeToString(),
        headers=PROTO_HEADERS,
    )
    msg = parse_proto_response(resp, pb.AuthorResponse(), f"POST /authors (Protobuf) → Create '{name}'")
    if msg is None:
        raise RuntimeError(f"Create author failed for '{name}'")
    return msg.author


def list_authors_proto() -> pb.AuthorListResponse:
    """GET /authors — receive Protobuf response."""
    resp = requests.get(
        f"{BASE_URL}/authors/",
        headers={"Accept": "application/x-protobuf"},
    )
    msg = parse_proto_response(resp, pb.AuthorListResponse(), "GET /authors (Protobuf)")
    if msg is None:
        raise RuntimeError("List authors failed")
    return msg


def create_book_proto(title: str, isbn: str, year: int, author_ids: list[int], copies: int) -> pb.Book:
    """POST /books — send and receive Protobuf."""
    req = pb.CreateBookRequest(
        title=title,
        isbn=isbn,
        published_year=year,
        author_ids=author_ids,
        copies_count=copies,
    )
    resp = requests.post(
        f"{BASE_URL}/books/",
        data=req.SerializeToString(),
        headers=PROTO_HEADERS,
    )
    msg = parse_proto_response(resp, pb.BookResponse(), f"POST /books (Protobuf) → Create '{title}'")
    if msg is None:
        raise RuntimeError(f"Create book failed for '{title}'")
    return msg.book


def list_books_proto() -> pb.BookListResponse:
    """GET /books — receive Protobuf response."""
    resp = requests.get(
        f"{BASE_URL}/books/",
        headers={"Accept": "application/x-protobuf"},
    )
    msg = parse_proto_response(resp, pb.BookListResponse(), "GET /books (Protobuf)")
    if msg is None:
        raise RuntimeError("List books failed")
    return msg


def create_member_proto(name: str, email: str, phone: str) -> pb.Member:
    """POST /members — send and receive Protobuf."""
    req = pb.CreateMemberRequest(name=name, email=email, phone=phone)
    resp = requests.post(
        f"{BASE_URL}/members/",
        data=req.SerializeToString(),
        headers=PROTO_HEADERS,
    )
    msg = parse_proto_response(resp, pb.MemberResponse(), f"POST /members (Protobuf) → Create '{name}'")
    if msg is None:
        raise RuntimeError(f"Create member failed for '{name}'")
    return msg.member


def borrow_book_proto(copy_id: int, member_id: int, due_days: int = 14) -> pb.BorrowTransaction:
    """POST /loans — send and receive Protobuf."""
    due = datetime.now(timezone.utc) + timedelta(days=due_days)
    req = pb.BorrowRequest(
        copy_id=copy_id,
        member_id=member_id,
        due_date=to_ts(due),
    )
    resp = requests.post(
        f"{BASE_URL}/loans/",
        data=req.SerializeToString(),
        headers=PROTO_HEADERS,
    )
    msg = parse_proto_response(resp, pb.TransactionResponse(), "POST /loans (Protobuf) → Borrow book")
    if msg is None:
        raise RuntimeError("Borrow book failed")
    return msg.transaction


def return_book_proto(transaction_id: int) -> pb.BorrowTransaction:
    """POST /loans/{id}/return — send and receive Protobuf."""
    req = pb.ReturnRequest(transaction_id=transaction_id, fine_per_day=0.50)
    resp = requests.post(
        f"{BASE_URL}/loans/{transaction_id}/return",
        data=req.SerializeToString(),
        headers=PROTO_HEADERS,
    )
    msg = parse_proto_response(resp, pb.TransactionResponse(), f"POST /loans/{transaction_id}/return (Protobuf)")
    if msg is None:
        raise RuntimeError(f"Return book failed for transaction {transaction_id}")
    return msg.transaction


def get_borrowed_books_proto(member_id: int | None = None) -> pb.TransactionListResponse:
    """GET /loans/borrowed — receive Protobuf."""
    url = f"{BASE_URL}/loans/borrowed"
    if member_id:
        url += f"?member_id={member_id}"
    resp = requests.get(url, headers={"Accept": "application/x-protobuf"})
    msg = parse_proto_response(resp, pb.TransactionListResponse(), "GET /loans/borrowed (Protobuf)")
    if msg is None:
        raise RuntimeError("Get borrowed books failed")
    return msg


def get_due_books_proto() -> pb.TransactionListResponse:
    """GET /loans/due — receive Protobuf."""
    resp = requests.get(
        f"{BASE_URL}/loans/due",
        headers={"Accept": "application/x-protobuf"},
    )
    msg = parse_proto_response(resp, pb.TransactionListResponse(), "GET /loans/due (Protobuf)")
    if msg is None:
        raise RuntimeError("Get due books failed")
    return msg


def get_fines_proto(transaction_id: int) -> pb.FineListResponse:
    """GET /loans/{id}/fines — receive Protobuf."""
    resp = requests.get(
        f"{BASE_URL}/loans/{transaction_id}/fines",
        headers={"Accept": "application/x-protobuf"},
    )
    msg = parse_proto_response(resp, pb.FineListResponse(), f"GET /loans/{transaction_id}/fines (Protobuf)")
    if msg is None:
        raise RuntimeError(f"Get fines failed for transaction {transaction_id}")
    return msg


def pay_fines_proto(fine_ids: list[int]) -> pb.FineListResponse:
    """POST /loans/fines/pay — send and receive Protobuf."""
    req = pb.PayFinesRequest(fine_ids=fine_ids)
    resp = requests.post(
        f"{BASE_URL}/loans/fines/pay",
        data=req.SerializeToString(),
        headers=PROTO_HEADERS,
    )
    msg = parse_proto_response(resp, pb.FineListResponse(), "POST /loans/fines/pay (Protobuf)")
    if msg is None:
        raise RuntimeError("Pay fines failed")
    return msg


def get_stats_proto() -> pb.LibraryStats:
    """GET /loans/stats — receive Protobuf."""
    resp = requests.get(
        f"{BASE_URL}/loans/stats",
        headers={"Accept": "application/x-protobuf"},
    )
    msg = parse_proto_response(resp, pb.LibraryStats(), "GET /loans/stats (Protobuf)")
    if msg is None:
        raise RuntimeError("Get stats failed")
    return msg


# ─── Main demo flow ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    print_section("1. Create Author (Protobuf)")
    author = create_author_proto("George Orwell")

    print_section("2. List Authors (Protobuf)")
    list_authors_proto()

    print_section("3. Create Book with 2 copies (Protobuf)")
    book = create_book_proto(
        title="1984",
        isbn="978-0451524935-proto",
        year=1949,
        author_ids=[author.author_id],
        copies=2,
    )
    copy_id = book.copies[0].copy_id if book.copies else 1

    print_section("4. List Books (Protobuf)")
    list_books_proto()

    print_section("5. Create Member (Protobuf)")
    member = create_member_proto("Alice Proto", "alice_proto@example.com", "+91-9999999999")

    print_section("6. Borrow Book (Protobuf)")
    tx = borrow_book_proto(copy_id=copy_id, member_id=member.member_id)

    print_section("7. Get Borrowed Books for Member (Protobuf)")
    get_borrowed_books_proto(member_id=member.member_id)

    print_section("8. Get Overdue Books (Protobuf)")
    get_due_books_proto()

    print_section("9. Return Book (Protobuf)")
    tx = return_book_proto(transaction_id=tx.transaction_id)

    print_section("10. Get Fines for Transaction (Protobuf)")
    fines = get_fines_proto(transaction_id=tx.transaction_id)
    fine_ids = [f.fine_id for f in fines.fines]

    if fine_ids:
        print_section("11. Pay Fines (Protobuf)")
        pay_fines_proto(fine_ids=fine_ids)

    print_section("12. Library Statistics (Protobuf)")
    get_stats_proto()

    print("\n✅  All Protobuf demo calls complete!")
