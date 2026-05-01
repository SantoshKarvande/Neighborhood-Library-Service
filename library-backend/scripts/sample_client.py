#!/usr/bin/env python3
"""
sample_client.py – Demonstrates every REST endpoint via httpx.

Usage:
    pip install httpx
    python scripts/sample_client.py
"""

import httpx
from datetime import datetime, timedelta, timezone

BASE = "http://localhost:8000/api/v1"


def p(label: str, r: httpx.Response):
    print(f"\n{'='*60}")
    print(f"  {label}  [{r.status_code}]")
    print(f"{'='*60}")
    try:
        import json
        print(json.dumps(r.json(), indent=2, default=str))
    except Exception:
        print(r.text)


with httpx.Client(timeout=10) as c:

    # ── Health ─────────────────────────────────────────────────────────────────
    p("GET /", c.get("http://localhost:8000/"))

    # ── Authors ────────────────────────────────────────────────────────────────
    p("POST /authors (create)", c.post(f"{BASE}/authors", json={"name": "George Orwell"}))
    orwell_id = c.post(f"{BASE}/authors", json={"name": "Frank Herbert"}).json().get("author_id")

    p("GET /authors", c.get(f"{BASE}/authors"))

    # ── Books ──────────────────────────────────────────────────────────────────
    book_payload = {
        "title": "1984",
        "isbn": "978-0451524935",
        "published_year": 1949,
        "author_ids": [1],
        "copies_count": 2,
    }
    r_book = c.post(f"{BASE}/books", json=book_payload)
    p("POST /books (create)", r_book)
    book_id = r_book.json().get("book_id", 1)

    p(f"GET /books/{book_id}", c.get(f"{BASE}/books/{book_id}"))
    p(f"GET /books/{book_id}/copies", c.get(f"{BASE}/books/{book_id}/copies"))

    p(
        f"PATCH /books/{book_id}",
        c.patch(f"{BASE}/books/{book_id}", json={"published_year": 1948}),
    )
    p("GET /books?available_only=true", c.get(f"{BASE}/books?available_only=true"))

    # ── Members ────────────────────────────────────────────────────────────────
    r_member = c.post(
        f"{BASE}/members",
        json={"name": "Alice Sharma", "email": "alice@example.com", "phone": "+91-9000000001"},
    )
    p("POST /members (create)", r_member)
    member_id = r_member.json().get("member_id", 1)

    p(f"GET /members/{member_id}", c.get(f"{BASE}/members/{member_id}"))

    # ── Borrow ─────────────────────────────────────────────────────────────────
    copy_id = c.get(f"{BASE}/books/{book_id}/copies").json()[0]["copy_id"]

    due = (datetime.now(timezone.utc) + timedelta(days=14)).isoformat()
    r_loan = c.post(
        f"{BASE}/loans",
        json={"copy_id": copy_id, "member_id": member_id, "due_date": due},
    )
    p("POST /loans (borrow)", r_loan)
    tx_id = r_loan.json().get("transaction_id", 1)

    # ── Queries ────────────────────────────────────────────────────────────────
    p("GET /loans/borrowed", c.get(f"{BASE}/loans/borrowed"))
    p(f"GET /loans/borrowed?member_id={member_id}", c.get(f"{BASE}/loans/borrowed?member_id={member_id}"))
    p("GET /loans/due (overdue)", c.get(f"{BASE}/loans/due"))
    p("GET /loans/stats", c.get(f"{BASE}/loans/stats"))

    # ── Return (simulate overdue) ──────────────────────────────────────────────
    p(
        f"POST /loans/{tx_id}/return",
        c.post(f"{BASE}/loans/{tx_id}/return", json={"fine_per_day": 0.50}),
    )

    # ── Fines ──────────────────────────────────────────────────────────────────
    p(f"GET /loans/{tx_id}/fines", c.get(f"{BASE}/loans/{tx_id}/fines"))
    p(
        f"GET /loans/members/{member_id}/fines?unpaid_only=true",
        c.get(f"{BASE}/loans/members/{member_id}/fines?unpaid_only=true"),
    )

    fines = c.get(f"{BASE}/loans/{tx_id}/fines").json()
    if fines:
        fine_ids = [f["fine_id"] for f in fines]
        p("POST /loans/fines/pay", c.post(f"{BASE}/loans/fines/pay", json={"fine_ids": fine_ids}))

    # ── Mark overdue (admin) ───────────────────────────────────────────────────
    p("POST /loans/mark-overdue", c.post(f"{BASE}/loans/mark-overdue"))

    print("\n✅  All sample calls complete.")

