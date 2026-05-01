"""
SQLAlchemy ORM models — mirrors db_schema.sql exactly.

Tables:
    authors, books, book_authors, book_copies,
    members, borrow_transactions, fines

Enums:
    book_status   : AVAILABLE | BORROWED | RESERVED | LOST
    transaction_status : BORROWED | RETURNED | OVERDUE
"""

import enum
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    BigInteger, Boolean, CheckConstraint, Column, Date,
    DateTime, Enum as SAEnum, ForeignKey, Integer,
    Numeric, String, Text, UniqueConstraint, func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# ─── Enum Definitions ──────────────────────────────────────────────────────────

class BookStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    BORROWED  = "BORROWED"
    RESERVED  = "RESERVED"
    LOST      = "LOST"


class TransactionStatus(str, enum.Enum):
    BORROWED = "BORROWED"
    RETURNED = "RETURNED"
    OVERDUE  = "OVERDUE"


# ─── Base ──────────────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


# ─── Authors ───────────────────────────────────────────────────────────────────

class Author(Base):
    __tablename__ = "authors"

    author_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str]      = mapped_column(Text, nullable=False)

    # relationships
    book_authors: Mapped[List["BookAuthor"]] = relationship(
        "BookAuthor", back_populates="author", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Author id={self.author_id} name={self.name!r}>"


# ─── Books ─────────────────────────────────────────────────────────────────────

class Book(Base):
    __tablename__ = "books"

    book_id:        Mapped[int]           = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    title:          Mapped[str]           = mapped_column(Text, nullable=False)
    isbn:           Mapped[Optional[str]] = mapped_column(String(20), unique=True, nullable=True)
    published_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at:     Mapped[datetime]      = mapped_column(DateTime, server_default=func.now())

    # relationships
    book_authors: Mapped[List["BookAuthor"]] = relationship(
        "BookAuthor", back_populates="book", cascade="all, delete-orphan"
    )
    copies: Mapped[List["BookCopy"]] = relationship(
        "BookCopy", back_populates="book", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Book id={self.book_id} title={self.title!r}>"


# ─── Book ↔ Author mapping ─────────────────────────────────────────────────────

class BookAuthor(Base):
    __tablename__ = "book_authors"

    book_id:   Mapped[int] = mapped_column(BigInteger, ForeignKey("books.book_id",   ondelete="CASCADE"), primary_key=True)
    author_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("authors.author_id", ondelete="CASCADE"), primary_key=True)

    book:   Mapped["Book"]   = relationship("Book",   back_populates="book_authors")
    author: Mapped["Author"] = relationship("Author", back_populates="book_authors")


# ─── Book Copies ───────────────────────────────────────────────────────────────

class BookCopy(Base):
    __tablename__ = "book_copies"

    copy_id:    Mapped[int]        = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    book_id:    Mapped[int]        = mapped_column(BigInteger, ForeignKey("books.book_id", ondelete="CASCADE"), nullable=False)
    status:     Mapped[BookStatus] = mapped_column(
        SAEnum(BookStatus, name="book_status", create_type=False),
        nullable=False, server_default="AVAILABLE"
    )
    created_at: Mapped[datetime]   = mapped_column(DateTime, server_default=func.now())

    book:         Mapped["Book"]                = relationship("Book",    back_populates="copies")
    transactions: Mapped[List["BorrowTransaction"]] = relationship(
        "BorrowTransaction", back_populates="copy"
    )

    def __repr__(self) -> str:
        return f"<BookCopy id={self.copy_id} book_id={self.book_id} status={self.status}>"


# ─── Members ───────────────────────────────────────────────────────────────────

class Member(Base):
    __tablename__ = "members"

    member_id:  Mapped[int]           = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name:       Mapped[str]           = mapped_column(Text, nullable=False)
    email:      Mapped[Optional[str]] = mapped_column(Text, unique=True, nullable=True)
    phone:      Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime]      = mapped_column(DateTime, server_default=func.now())

    transactions: Mapped[List["BorrowTransaction"]] = relationship(
        "BorrowTransaction", back_populates="member"
    )

    def __repr__(self) -> str:
        return f"<Member id={self.member_id} name={self.name!r}>"


# ─── Borrow Transactions ───────────────────────────────────────────────────────

class BorrowTransaction(Base):
    __tablename__ = "borrow_transactions"
    __table_args__ = (
        CheckConstraint(
            "return_date IS NULL OR return_date >= borrow_date",
            name="chk_return_date",
        ),
    )

    transaction_id: Mapped[int]               = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    copy_id:        Mapped[int]               = mapped_column(BigInteger, ForeignKey("book_copies.copy_id"), nullable=False)
    member_id:      Mapped[int]               = mapped_column(BigInteger, ForeignKey("members.member_id"), nullable=False)
    borrow_date:    Mapped[datetime]          = mapped_column(DateTime, server_default=func.now())
    due_date:       Mapped[datetime]          = mapped_column(DateTime, nullable=False)
    return_date:    Mapped[Optional[datetime]]= mapped_column(DateTime, nullable=True)
    status:         Mapped[TransactionStatus] = mapped_column(
        SAEnum(TransactionStatus, name="transaction_status", create_type=False),
        nullable=False, server_default="BORROWED"
    )

    copy:   Mapped["BookCopy"] = relationship("BookCopy", back_populates="transactions")
    member: Mapped["Member"]   = relationship("Member",   back_populates="transactions")
    fines:  Mapped[List["Fine"]] = relationship("Fine", back_populates="transaction")

    def __repr__(self) -> str:
        return f"<BorrowTransaction id={self.transaction_id} status={self.status}>"


# ─── Fines ─────────────────────────────────────────────────────────────────────

class Fine(Base):
    __tablename__ = "fines"

    fine_id:        Mapped[int]      = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    transaction_id: Mapped[int]      = mapped_column(BigInteger, ForeignKey("borrow_transactions.transaction_id"), nullable=False)
    amount:         Mapped[float]    = mapped_column(Numeric(10, 2), nullable=False)
    paid:           Mapped[bool]     = mapped_column(Boolean, nullable=False, server_default="false")
    created_at:     Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    transaction: Mapped["BorrowTransaction"] = relationship("BorrowTransaction", back_populates="fines")

    def __repr__(self) -> str:
        return f"<Fine id={self.fine_id} amount={self.amount} paid={self.paid}>"



