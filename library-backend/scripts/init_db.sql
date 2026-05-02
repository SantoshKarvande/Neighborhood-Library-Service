-- =============================================================================
-- init_db.sql
-- Runs once on first container start (docker-entrypoint-initdb.d).
-- Executed as the POSTGRES_USER superuser (postgres).
--
-- What it does:
--   1. Drops the library_db database if it already exists
--   2. Drops the library_user role if it already exists
--   3. Re-creates library_user with a password
--   4. Re-creates library_db owned by library_user
--   5. Grants full privileges on all current and future objects
-- =============================================================================

-- ── Step 1: Drop existing connections to library_db (so DROP DATABASE works) --
SELECT pg_terminate_backend(pid)
FROM   pg_stat_activity
WHERE  datname = 'library_db'
  AND  pid <> pg_backend_pid();

-- ── Step 2: Drop DB and user (order matters — drop DB before role) ────────────
DROP DATABASE IF EXISTS library_db;
DROP ROLE     IF EXISTS library_user;

-- ── Step 3: Create user ───────────────────────────────────────────────────────
CREATE ROLE library_user
    WITH LOGIN
         PASSWORD 'library_pass'
         CREATEDB;          -- allows the user to create DBs if needed

-- ── Step 4: Create database owned by library_user ────────────────────────────
CREATE DATABASE library_db
    OWNER     = library_user
    ENCODING  = 'UTF8'
    LC_COLLATE = 'en_US.utf8'
    LC_CTYPE   = 'en_US.utf8'
    TEMPLATE  = template0;

-- ── Step 5: Connect to library_db and grant all privileges ───────────────────
\connect library_db

-- Grant all on the public schema itself
GRANT ALL ON SCHEMA public TO library_user;
ALTER  SCHEMA public OWNER TO library_user;

-- Grant on all EXISTING tables, sequences, functions (idempotent re-run safe)
GRANT ALL PRIVILEGES ON ALL TABLES     IN SCHEMA public TO library_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES  IN SCHEMA public TO library_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS  IN SCHEMA public TO library_user;

-- Grant on all FUTURE tables, sequences, functions created in this schema
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL ON TABLES    TO library_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL ON SEQUENCES TO library_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL ON FUNCTIONS TO library_user;

-- ── Done ──────────────────────────────────────────────────────────────────────
-- library_user now has full read/write/execute access to library_db.
-- Alembic will run next and create all tables.
