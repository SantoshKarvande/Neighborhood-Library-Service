"""
Service layer for Book, BookAuthor, and BookCopy operations.
"""

from typing import Optional, Sequence

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import Author, Book, BookAuthor, BookCopy, BookStatus
from app.schemas.schemas import BookCreate, BookCopyStatusUpdate, BookUpdate


# ─── helpers ──────────────────────────────────────────────────────────────────

def _book_options():
    return [
        selectinload(Book.book_authors).selectinload(BookAuthor.author),
        selectinload(Book.copies),
    ]


async def get_or_404(db: AsyncSession, book_id: int) -> Book:
    row = (
        await db.execute(
            select(Book).options(*_book_options()).where(Book.book_id == book_id)
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Book {book_id} not found")
    return row


async def _resolve_authors(db: AsyncSession, ids: list[int]) -> list[Author]:
    rows = (await db.execute(select(Author).where(Author.author_id.in_(ids)))).scalars().all()
    found_ids = {a.author_id for a in rows}
    missing   = set(ids) - found_ids
    if missing:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Author IDs not found: {sorted(missing)}",
        )
    return list(rows)


# ─── Book CRUD ────────────────────────────────────────────────────────────────

async def list_books(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    author_id: Optional[int] = None,
    available_only: bool = False,
) -> tuple[int, Sequence[Book]]:
    q = select(Book).options(*_book_options())

    if search:
        q = q.where(Book.title.ilike(f"%{search}%"))

    if author_id is not None:
        q = q.join(BookAuthor, BookAuthor.book_id == Book.book_id).where(
            BookAuthor.author_id == author_id
        )

    if available_only:
        q = q.join(BookCopy, BookCopy.book_id == Book.book_id).where(
            BookCopy.status == BookStatus.AVAILABLE
        ).distinct()

    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows  = (await db.execute(q.order_by(Book.title).offset(skip).limit(limit))).scalars().all()
    return total, rows


async def get_book(db: AsyncSession, book_id: int) -> Book:
    return await get_or_404(db, book_id)


async def create_book(db: AsyncSession, data: BookCreate) -> Book:
    # ISBN uniqueness check
    if data.isbn:
        existing = (
            await db.execute(select(Book).where(Book.isbn == data.isbn))
        ).scalar_one_or_none()
        if existing:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"ISBN '{data.isbn}' already registered (book_id={existing.book_id})",
            )

    book = Book(title=data.title, isbn=data.isbn, published_year=data.published_year)
    db.add(book)
    await db.flush()   # get book_id before linking

    # link authors
    authors = await _resolve_authors(db, data.author_ids)
    for author in authors:
        db.add(BookAuthor(book_id=book.book_id, author_id=author.author_id))

    # create physical copies
    for _ in range(data.copies_count):
        db.add(BookCopy(book_id=book.book_id, status=BookStatus.AVAILABLE))

    await db.commit()
    return await get_or_404(db, book.book_id)


async def update_book(db: AsyncSession, book_id: int, data: BookUpdate) -> Book:
    book = await get_or_404(db, book_id)
    updates = data.model_dump(exclude_unset=True)

    if "isbn" in updates and updates["isbn"] != book.isbn:
        existing = (
            await db.execute(
                select(Book).where(Book.isbn == updates["isbn"], Book.book_id != book_id)
            )
        ).scalar_one_or_none()
        if existing:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"ISBN '{updates['isbn']}' already belongs to book_id={existing.book_id}",
            )

    if "author_ids" in updates:
        author_ids = updates.pop("author_ids") or []
        # remove old links
        for ba in list(book.book_authors):
            await db.delete(ba)
        await db.flush()
        # add new links
        authors = await _resolve_authors(db, author_ids)
        for author in authors:
            db.add(BookAuthor(book_id=book.book_id, author_id=author.author_id))

    for field, val in updates.items():
        setattr(book, field, val)

    await db.commit()
    return await get_or_404(db, book_id)


async def delete_book(db: AsyncSession, book_id: int) -> None:
    book = await get_or_404(db, book_id)

    # Guard: cannot delete if any copy is currently borrowed
    borrowed = [c for c in book.copies if c.status == BookStatus.BORROWED]
    if borrowed:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Book has {len(borrowed)} copy/copies currently borrowed; return them first.",
        )

    await db.delete(book)
    await db.commit()


# ─── Book Copy management ─────────────────────────────────────────────────────

async def add_copies(db: AsyncSession, book_id: int, count: int) -> Book:
    book = await get_or_404(db, book_id)
    for _ in range(count):
        db.add(BookCopy(book_id=book.book_id, status=BookStatus.AVAILABLE))
    await db.commit()
    return await get_or_404(db, book_id)


async def get_copy_or_404(db: AsyncSession, copy_id: int) -> BookCopy:
    row = await db.get(BookCopy, copy_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"BookCopy {copy_id} not found")
    return row


async def update_copy_status(
    db: AsyncSession, copy_id: int, data: BookCopyStatusUpdate
) -> BookCopy:
    copy = await get_copy_or_404(db, copy_id)
    copy.status = data.status
    await db.commit()
    await db.refresh(copy)
    return copy


async def list_copies(
    db: AsyncSession,
    book_id: int,
    status_filter: Optional[BookStatus] = None,
) -> Sequence[BookCopy]:
    q = select(BookCopy).where(BookCopy.book_id == book_id)
    if status_filter:
        q = q.where(BookCopy.status == status_filter)
    return (await db.execute(q.order_by(BookCopy.copy_id))).scalars().all()


