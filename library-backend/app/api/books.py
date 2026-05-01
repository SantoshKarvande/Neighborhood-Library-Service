from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.models import BookStatus
from app.schemas.schemas import (
    BookCopyCreate, BookCopyResponse, BookCopyStatusUpdate,
    BookCreate, BookResponse, BookUpdate,
)
from app.services import books_service

router = APIRouter(prefix="/books", tags=["Books"])


# ─── Book CRUD ────────────────────────────────────────────────────────────────

@router.get("/", response_model=dict)
async def list_books(
    skip:           int            = Query(0, ge=0),
    limit:          int            = Query(20, ge=1, le=100),
    search:         Optional[str]  = Query(None, description="Search by title"),
    author_id:      Optional[int]  = Query(None, description="Filter by author ID"),
    available_only: bool           = Query(False, description="Only books with ≥1 AVAILABLE copy"),
    db: AsyncSession               = Depends(get_db),
):
    """List books with optional filtering."""
    total, rows = await books_service.list_books(db, skip, limit, search, author_id, available_only)
    return {
        "total": total, "skip": skip, "limit": limit,
        "items": [BookResponse.model_validate(r) for r in rows],
    }


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(book_id: int, db: AsyncSession = Depends(get_db)):
    """Retrieve full details of a single book including authors and all copies."""
    return await books_service.get_book(db, book_id)


@router.post("/", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(data: BookCreate, db: AsyncSession = Depends(get_db)):
    """
    Add a new book. Optionally link existing authors by `author_ids`
    and specify `copies_count` to create that many physical copies immediately.
    """
    return await books_service.create_book(db, data)


@router.patch("/{book_id}", response_model=BookResponse)
async def update_book(
    book_id: int, data: BookUpdate, db: AsyncSession = Depends(get_db)
):
    """Partially update book metadata. Sending `author_ids` replaces the full author list."""
    return await books_service.update_book(db, book_id, data)


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a book and all its copies (only if no copies are currently borrowed)."""
    await books_service.delete_book(db, book_id)


# ─── Copy management ──────────────────────────────────────────────────────────

@router.get("/{book_id}/copies", response_model=list[BookCopyResponse])
async def list_copies(
    book_id:       int                  = ...,
    status_filter: Optional[BookStatus] = Query(None, alias="status"),
    db: AsyncSession                    = Depends(get_db),
):
    """List all physical copies of a book, optionally filtered by status."""
    return await books_service.list_copies(db, book_id, status_filter)


@router.post("/{book_id}/copies", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def add_copies(
    book_id: int,
    count:   int = Query(1, ge=1, le=50, description="Number of new copies to add"),
    db: AsyncSession = Depends(get_db),
):
    """Add one or more new physical copies to an existing book."""
    return await books_service.add_copies(db, book_id, count)


@router.patch("/copies/{copy_id}/status", response_model=BookCopyResponse)
async def update_copy_status(
    copy_id: int, data: BookCopyStatusUpdate, db: AsyncSession = Depends(get_db)
):
    """Manually update a copy's status (e.g., mark as LOST)."""
    return await books_service.update_copy_status(db, copy_id, data)


