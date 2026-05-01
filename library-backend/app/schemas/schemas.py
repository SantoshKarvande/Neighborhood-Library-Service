"""
Pydantic v2 schemas for every API surface.

Naming convention:
    <Entity>Create   – POST body
    <Entity>Update   – PATCH body  (all fields optional)
    <Entity>Response – response body
"""

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, model_validator


# ══════════════════════════════════════════════════════════════════════════════
# Enums (re-exported as plain strings for OpenAPI clarity)
# ══════════════════════════════════════════════════════════════════════════════

from app.models.models import BookStatus, TransactionStatus   # noqa: E402


# ══════════════════════════════════════════════════════════════════════════════
# Author
# ══════════════════════════════════════════════════════════════════════════════

class AuthorBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, examples=["George Orwell"])


class AuthorCreate(AuthorBase):
    pass


class AuthorUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)


class AuthorResponse(AuthorBase):
    author_id: int

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════════════════════
# Book
# ══════════════════════════════════════════════════════════════════════════════

class BookCreate(BaseModel):
    title:          str            = Field(..., min_length=1, examples=["1984"])
    isbn:           Optional[str]  = Field(None, max_length=20, examples=["978-0451524935"])
    published_year: Optional[int]  = Field(None, ge=1000, le=2100, examples=[1949])
    author_ids:     List[int]      = Field(default_factory=list, description="List of existing author IDs to link")
    copies_count:   int            = Field(1, ge=1, le=100, description="Number of physical copies to create on add")


class BookUpdate(BaseModel):
    title:          Optional[str] = Field(None, min_length=1)
    isbn:           Optional[str] = Field(None, max_length=20)
    published_year: Optional[int] = Field(None, ge=1000, le=2100)
    author_ids:     Optional[List[int]] = Field(None, description="Replaces the full author list when provided")


class BookCopyResponse(BaseModel):
    copy_id:    int
    status:     BookStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class BookResponse(BaseModel):
    book_id:        int
    title:          str
    isbn:           Optional[str]
    published_year: Optional[int]
    created_at:     datetime
    authors:        List[AuthorResponse] = []
    copies:         List[BookCopyResponse] = []

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════════════════════
# Book Copy
# ══════════════════════════════════════════════════════════════════════════════

class BookCopyCreate(BaseModel):
    book_id: int = Field(..., gt=0)
    count:   int = Field(1, ge=1, le=50, description="Number of copies to add")


class BookCopyStatusUpdate(BaseModel):
    status: BookStatus


# ══════════════════════════════════════════════════════════════════════════════
# Member
# ══════════════════════════════════════════════════════════════════════════════

class MemberCreate(BaseModel):
    name:  str                  = Field(..., min_length=1, examples=["Alice Smith"])
    email: Optional[EmailStr]   = Field(None, examples=["alice@example.com"])
    phone: Optional[str]        = Field(None, max_length=30, examples=["+1-555-0100"])


class MemberUpdate(BaseModel):
    name:  Optional[str]      = Field(None, min_length=1)
    email: Optional[EmailStr] = None
    phone: Optional[str]      = Field(None, max_length=30)


class MemberResponse(BaseModel):
    member_id:  int
    name:       str
    email:      Optional[str]
    phone:      Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════════════════════
# Borrow / Return
# ══════════════════════════════════════════════════════════════════════════════

class BorrowRequest(BaseModel):
    """Body for POST /loans  (borrow a book)."""
    copy_id:   int      = Field(..., gt=0, description="Specific copy to borrow")
    member_id: int      = Field(..., gt=0)
    due_date:  datetime = Field(..., description="Expected return deadline (UTC)")

    @model_validator(mode="after")
    def due_must_be_future(self) -> "BorrowRequest":
        due_date = self.due_date
        if due_date.tzinfo is None:
            due_date = due_date.replace(tzinfo=timezone.utc)
        else:
            due_date = due_date.astimezone(timezone.utc)

        if due_date <= datetime.now(timezone.utc):
            raise ValueError("due_date must be in the future")
        return self


class ReturnRequest(BaseModel):
    """Body for POST /loans/{transaction_id}/return."""
    fine_per_day: float = Field(
        0.50, ge=0, description="Fine rate in currency units per overdue day"
    )


class FineResponse(BaseModel):
    fine_id:        int
    transaction_id: int
    amount:         float
    paid:           bool
    created_at:     datetime

    model_config = {"from_attributes": True}


class TransactionResponse(BaseModel):
    transaction_id: int
    copy_id:        int
    member_id:      int
    borrow_date:    datetime
    due_date:       datetime
    return_date:    Optional[datetime]
    status:         TransactionStatus
    fines:          List[FineResponse] = []

    # enriched from joins
    book_title:     Optional[str] = None
    member_name:    Optional[str] = None

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════════════════════
# Fine payment
# ══════════════════════════════════════════════════════════════════════════════

class FinePayRequest(BaseModel):
    fine_ids: List[int] = Field(..., min_length=1, description="IDs of fines to mark as paid")


# ══════════════════════════════════════════════════════════════════════════════
# Statistics / dashboard
# ══════════════════════════════════════════════════════════════════════════════

class LibraryStats(BaseModel):
    total_books:         int
    total_copies:        int
    available_copies:    int
    total_members:       int
    active_loans:        int
    overdue_loans:       int
    total_fines_unpaid:  float


# ══════════════════════════════════════════════════════════════════════════════
# Pagination envelope
# ══════════════════════════════════════════════════════════════════════════════

class Paginated(BaseModel):
    total:  int
    skip:   int
    limit:  int
    items:  list

