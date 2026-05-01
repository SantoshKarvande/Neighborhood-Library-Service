"""initial schema – matches db_schema.sql exactly

Revision ID: 0001_initial
Revises:
Create Date: 2025-01-01 00:00:00
"""

from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Enums ──────────────────────────────────────────────────────────────────
    # Use DO blocks so migration is idempotent regardless of whether
    # init_db.sql was already run (avoids DuplicateObjectError).
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE if not exists book_status AS ENUM ('AVAILABLE','BORROWED','RESERVED','LOST');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE if not exists transaction_status AS ENUM ('BORROWED','RETURNED','OVERDUE');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # ── authors ────────────────────────────────────────────────────────────────
    op.create_table(
        "authors",
        sa.Column("author_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("name",      sa.Text(),       nullable=False),
    )

    # ── books ──────────────────────────────────────────────────────────────────
    op.create_table(
        "books",
        sa.Column("book_id",        sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("title",          sa.Text(),       nullable=False),
        sa.Column("isbn",           sa.String(20),   unique=True, nullable=True),
        sa.Column("published_year", sa.Integer(),    nullable=True),
        sa.Column("created_at",     sa.DateTime(),   server_default=sa.func.now()),
    )

    # ── book_authors ───────────────────────────────────────────────────────────
    op.create_table(
        "book_authors",
        sa.Column("book_id",   sa.BigInteger(),
                  sa.ForeignKey("books.book_id",   ondelete="CASCADE"), primary_key=True),
        sa.Column("author_id", sa.BigInteger(),
                  sa.ForeignKey("authors.author_id", ondelete="CASCADE"), primary_key=True),
    )

    # ── book_copies ────────────────────────────────────────────────────────────
    op.create_table(
        "book_copies",
        sa.Column("copy_id",    sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("book_id",    sa.BigInteger(),
                  sa.ForeignKey("books.book_id", ondelete="CASCADE"), nullable=False),
        sa.Column("status",     sa.Enum("AVAILABLE", "BORROWED", "RESERVED", "LOST",
                                        name="book_status", create_type=False),
                  nullable=False, server_default="AVAILABLE"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # ── members ────────────────────────────────────────────────────────────────
    op.create_table(
        "members",
        sa.Column("member_id",  sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("name",       sa.Text(),       nullable=False),
        sa.Column("email",      sa.Text(),       unique=True, nullable=True),
        sa.Column("phone",      sa.Text(),       nullable=True),
        sa.Column("created_at", sa.DateTime(),   server_default=sa.func.now()),
    )

    # ── borrow_transactions ────────────────────────────────────────────────────
    op.create_table(
        "borrow_transactions",
        sa.Column("transaction_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("copy_id",        sa.BigInteger(),
                  sa.ForeignKey("book_copies.copy_id"), nullable=False),
        sa.Column("member_id",      sa.BigInteger(),
                  sa.ForeignKey("members.member_id"), nullable=False),
        sa.Column("borrow_date",    sa.DateTime(),   server_default=sa.func.now()),
        sa.Column("due_date",       sa.DateTime(),   nullable=False),
        sa.Column("return_date",    sa.DateTime(),   nullable=True),
        sa.Column("status",         sa.Enum("BORROWED", "RETURNED", "OVERDUE",
                                            name="transaction_status", create_type=False),
                  nullable=False, server_default="BORROWED"),
        sa.CheckConstraint(
            "return_date IS NULL OR return_date >= borrow_date",
            name="chk_return_date",
        ),
    )

    # ── fines ──────────────────────────────────────────────────────────────────
    op.create_table(
        "fines",
        sa.Column("fine_id",        sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("transaction_id", sa.BigInteger(),
                  sa.ForeignKey("borrow_transactions.transaction_id"), nullable=False),
        sa.Column("amount",     sa.Numeric(10, 2), nullable=False),
        sa.Column("paid",       sa.Boolean(),      nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(),     server_default=sa.func.now()),
    )

    # ── Useful indexes ─────────────────────────────────────────────────────────
    op.create_index("ix_book_copies_book_id",           "book_copies",          ["book_id"])
    op.create_index("ix_book_copies_status",            "book_copies",          ["status"])
    op.create_index("ix_borrow_transactions_copy_id",   "borrow_transactions",  ["copy_id"])
    op.create_index("ix_borrow_transactions_member_id", "borrow_transactions",  ["member_id"])
    op.create_index("ix_borrow_transactions_status",    "borrow_transactions",  ["status"])
    op.create_index("ix_borrow_transactions_due_date",  "borrow_transactions",  ["due_date"])
    op.create_index("ix_fines_transaction_id",          "fines",                ["transaction_id"])
    op.create_index("ix_fines_paid",                    "fines",                ["paid"])


def downgrade() -> None:
    op.drop_table("fines")
    op.drop_table("borrow_transactions")
    op.drop_table("members")
    op.drop_table("book_copies")
    op.drop_table("book_authors")
    op.drop_table("books")
    op.drop_table("authors")
    op.execute("DROP TYPE IF EXISTS transaction_status")
    op.execute("DROP TYPE IF EXISTS book_status")



