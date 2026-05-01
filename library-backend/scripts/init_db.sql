-- This script runs once when the Postgres container first starts.
-- It creates the custom enum types so that Alembic's migration can
-- reference them with create_type=False.

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'book_status') THEN
        CREATE TYPE book_status AS ENUM ('AVAILABLE', 'BORROWED', 'RESERVED', 'LOST');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'transaction_status') THEN
        CREATE TYPE transaction_status AS ENUM ('BORROWED', 'RETURNED', 'OVERDUE');
    END IF;
END
$$;

