#!/usr/bin/env python3
"""
Seed the database with demo authors, books, copies, members, and a sample loan.

Usage:
    DATABASE_URL=postgresql+asyncpg://... python scripts/seed.py
"""

import asyncio
import os
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/library_db",
)

engine = create_async_engine(DATABASE_URL, echo=True)
Session = async_sessionmaker(engine, expire_on_commit=False)

# Import after engine so models register against the correct metadata
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.models.models import (   # noqa: E402
    Author, Book, BookAuthor, BookCopy, BookStatus,
    BorrowTransaction, Fine, Member, TransactionStatus,
)


async def seed():
    async with Session() as db:
        # Authors
        authors_data = [
            "George Orwell",
            "J.R.R. Tolkien",
            "Frank Herbert",
            "Ursula K. Le Guin",
        ]
        authors = []
        for name in authors_data:
            a = Author(name=name)
            db.add(a)
            authors.append(a)
        await db.flush()

        # Books
        books_raw = [
            dict(title="1984",                isbn="978-0451524935", published_year=1949, author_idx=0, copies=3),
            dict(title="Animal Farm",         isbn="978-0451526342", published_year=1945, author_idx=0, copies=2),
            dict(title="The Hobbit",          isbn="978-0547928227", published_year=1937, author_idx=1, copies=4),
            dict(title="Dune",                isbn="978-0441013593", published_year=1965, author_idx=2, copies=2),
            dict(title="The Left Hand of Darkness", isbn="978-0441478125", published_year=1969, author_idx=3, copies=1),
        ]

        books = []
        for bd in books_raw:
            b = Book(title=bd["title"], isbn=bd["isbn"], published_year=bd["published_year"])
            db.add(b)
            await db.flush()
            db.add(BookAuthor(book_id=b.book_id, author_id=authors[bd["author_idx"]].author_id))
            for _ in range(bd["copies"]):
                db.add(BookCopy(book_id=b.book_id, status=BookStatus.AVAILABLE))
            await db.flush()
            books.append(b)

        # Members
        members_data = [
            dict(name="Alice Sharma",  email="alice@example.com",  phone="+91-9000000001"),
            dict(name="Bob Mehta",     email="bob@example.com",    phone="+91-9000000002"),
            dict(name="Carol Patel",   email="carol@example.com",  phone="+91-9000000003"),
        ]
        members = []
        for md in members_data:
            m = Member(**md)
            db.add(m)
            members.append(m)
        await db.flush()

        # Fetch first available copy of "1984"
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        copy_row = (
            await db.execute(
                select(BookCopy)
                .where(BookCopy.book_id == books[0].book_id, BookCopy.status == BookStatus.AVAILABLE)
                .limit(1)
            )
        ).scalar_one_or_none()

        if copy_row:
            copy_row.status = BookStatus.BORROWED
            tx = BorrowTransaction(
                copy_id   = copy_row.copy_id,
                member_id = members[0].member_id,
                due_date  = datetime.utcnow() - timedelta(days=2),  # already overdue!
                status    = TransactionStatus.OVERDUE,
            )
            db.add(tx)
            await db.flush()
            # Attach fine
            db.add(Fine(transaction_id=tx.transaction_id, amount=1.00, paid=False))

        await db.commit()
        print("✅  Seed complete!")


if __name__ == "__main__":
    asyncio.run(seed())
