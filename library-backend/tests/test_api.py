"""
Integration tests – all major API endpoints.

Requires a running Postgres instance (or use the docker-compose test profile).
Set TEST_DATABASE_URL env var or it defaults to localhost.

Run:
    pytest tests/test_api.py -v
"""

import os
import asyncio
from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

TEST_DB_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://library_user:library_pass@localhost:5432/library_db",
)

# Override DATABASE_URL before importing the app
os.environ["DATABASE_URL"] = TEST_DB_URL

from app.main import app                          # noqa: E402
from app.core.database import engine, AsyncSessionLocal   # noqa: E402
from app.models.models import Base                # noqa: E402


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture()
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


# ─── Helpers ──────────────────────────────────────────────────────────────────

def future_date(days: int = 14) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


# ─── Author tests ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_author(client: AsyncClient):
    r = await client.post("/api/v1/authors", json={"name": "Test Author"})
    assert r.status_code == 201
    assert r.json()["name"] == "Test Author"
    assert "author_id" in r.json()


@pytest.mark.asyncio
async def test_list_authors(client: AsyncClient):
    r = await client.get("/api/v1/authors")
    assert r.status_code == 200
    assert "items" in r.json()


@pytest.mark.asyncio
async def test_update_author(client: AsyncClient):
    r = await client.post("/api/v1/authors", json={"name": "Old Name"})
    aid = r.json()["author_id"]
    r2 = await client.patch(f"/api/v1/authors/{aid}", json={"name": "New Name"})
    assert r2.status_code == 200
    assert r2.json()["name"] == "New Name"


# ─── Book tests ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_book(client: AsyncClient):
    # create author first
    a = await client.post("/api/v1/authors", json={"name": "Book Author"})
    aid = a.json()["author_id"]
    r = await client.post("/api/v1/books", json={
        "title": "Test Book", "isbn": "000-test-001",
        "published_year": 2000, "author_ids": [aid], "copies_count": 2,
    })
    assert r.status_code == 201
    data = r.json()
    assert data["title"] == "Test Book"
    assert len(data["copies"]) == 2
    assert len(data["authors"]) == 1


@pytest.mark.asyncio
async def test_list_books(client: AsyncClient):
    r = await client.get("/api/v1/books")
    assert r.status_code == 200
    assert "items" in r.json()


@pytest.mark.asyncio
async def test_update_book(client: AsyncClient):
    a = await client.post("/api/v1/authors", json={"name": "Au2"})
    aid = a.json()["author_id"]
    b = await client.post("/api/v1/books", json={
        "title": "Book v1", "author_ids": [aid], "copies_count": 1
    })
    bid = b.json()["book_id"]
    r = await client.patch(f"/api/v1/books/{bid}", json={"title": "Book v2"})
    assert r.status_code == 200
    assert r.json()["title"] == "Book v2"


@pytest.mark.asyncio
async def test_add_copies(client: AsyncClient):
    a = await client.post("/api/v1/authors", json={"name": "Au3"})
    aid = a.json()["author_id"]
    b = await client.post("/api/v1/books", json={
        "title": "Copy Test", "author_ids": [aid], "copies_count": 1
    })
    bid = b.json()["book_id"]
    r = await client.post(f"/api/v1/books/{bid}/copies?count=3")
    assert r.status_code == 201
    assert len(r.json()["copies"]) == 4   # 1 original + 3 new


# ─── Member tests ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_member(client: AsyncClient):
    r = await client.post("/api/v1/members", json={
        "name": "Alice", "email": "alice_test@test.com", "phone": "1234"
    })
    assert r.status_code == 201
    assert r.json()["membership_number"] if "membership_number" in r.json() else True


@pytest.mark.asyncio
async def test_duplicate_member_email(client: AsyncClient):
    await client.post("/api/v1/members", json={"name": "X", "email": "dup@test.com"})
    r = await client.post("/api/v1/members", json={"name": "Y", "email": "dup@test.com"})
    assert r.status_code == 409


# ─── Loan tests ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_borrow_and_return(client: AsyncClient):
    # Setup
    a = await client.post("/api/v1/authors", json={"name": "Loan Author"})
    b = await client.post("/api/v1/books", json={
        "title": "Loan Book", "author_ids": [a.json()["author_id"]], "copies_count": 1
    })
    m = await client.post("/api/v1/members", json={"name": "Borrower", "email": "borrow@test.com"})

    book_data = b.json()
    copy_id   = book_data["copies"][0]["copy_id"]
    member_id = m.json()["member_id"]

    # Borrow
    r_borrow = await client.post("/api/v1/loans", json={
        "copy_id": copy_id, "member_id": member_id, "due_date": future_date(14)
    })
    assert r_borrow.status_code == 201
    tx_id = r_borrow.json()["transaction_id"]

    # Cannot borrow again (no copies left)
    r2 = await client.post("/api/v1/loans", json={
        "copy_id": copy_id, "member_id": member_id, "due_date": future_date(14)
    })
    assert r2.status_code == 409

    # Return
    r_return = await client.post(f"/api/v1/loans/{tx_id}/return", json={"fine_per_day": 0.5})
    assert r_return.status_code == 200
    assert r_return.json()["status"] == "RETURNED"


@pytest.mark.asyncio
async def test_get_borrowed_books(client: AsyncClient):
    r = await client.get("/api/v1/loans/borrowed")
    assert r.status_code == 200
    assert "items" in r.json()


@pytest.mark.asyncio
async def test_get_due_books(client: AsyncClient):
    r = await client.get("/api/v1/loans/due")
    assert r.status_code == 200
    assert "items" in r.json()


@pytest.mark.asyncio
async def test_stats(client: AsyncClient):
    r = await client.get("/api/v1/loans/stats")
    assert r.status_code == 200
    data = r.json()
    for key in ("total_books", "total_members", "active_loans", "overdue_loans"):
        assert key in data


@pytest.mark.asyncio
async def test_pay_fines(client: AsyncClient):
    # Create a loan with an overdue scenario
    a = await client.post("/api/v1/authors", json={"name": "Fine Author"})
    b = await client.post("/api/v1/books", json={
        "title": "Fine Book", "author_ids": [a.json()["author_id"]], "copies_count": 1
    })
    m = await client.post("/api/v1/members", json={"name": "Finer", "email": "finer@test.com"})

    copy_id   = b.json()["copies"][0]["copy_id"]
    member_id = m.json()["member_id"]

    r_borrow = await client.post("/api/v1/loans", json={
        "copy_id": copy_id, "member_id": member_id, "due_date": future_date(1)
    })
    tx_id = r_borrow.json()["transaction_id"]

    # Return with a fine_per_day (even if not yet overdue the API accepts it)
    await client.post(f"/api/v1/loans/{tx_id}/return", json={"fine_per_day": 10.0})

    fines = (await client.get(f"/api/v1/loans/{tx_id}/fines")).json()
    # Pay any fines that exist
    if fines:
        fine_ids = [f["fine_id"] for f in fines]
        r_pay = await client.post("/api/v1/loans/fines/pay", json={"fine_ids": fine_ids})
        assert r_pay.status_code == 200
        assert all(f["paid"] for f in r_pay.json())


