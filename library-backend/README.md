# Neighborhood Library Service – Backend

A production-quality **Python / FastAPI** REST backend for the neighborhood library, backed by **PostgreSQL** and described by a **Protocol Buffers** interface definition.

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Database Schema](#database-schema)
3. [Quick Start (Docker Compose)](#quick-start-docker-compose)
4. [Local Development Setup](#local-development-setup)
5. [Running Database Migrations](#running-database-migrations)
6. [Running the Server](#running-the-server)
7. [Seeding Demo Data](#seeding-demo-data)
8. [Compiling the Proto File](#compiling-the-proto-file)
9. [API Reference](#api-reference)
10. [Running Tests](#running-tests)
11. [Sample Client](#sample-client)
12. [Environment Variables](#environment-variables)

---

## Project Structure

```
library-backend/
├── app/
│   ├── main.py                  # FastAPI app & lifespan
│   ├── core/
│   │   └── database.py          # Async SQLAlchemy engine + session
│   ├── models/
│   │   └── models.py            # ORM models (mirrors db_schema.sql exactly)
│   ├── schemas/
│   │   └── schemas.py           # Pydantic v2 request / response shapes
│   ├── services/
│   │   ├── authors_service.py   # Author business logic
│   │   ├── books_service.py     # Book + copy business logic
│   │   ├── members_service.py   # Member business logic
│   │   └── loans_service.py     # Borrow / return / fines / stats
│   └── api/
│       ├── authors.py           # /api/v1/authors
│       ├── books.py             # /api/v1/books
│       ├── members.py           # /api/v1/members
│       └── loans.py             # /api/v1/loans
│
├── migrations/
│   ├── env.py                   # Alembic async env
│   ├── script.py.mako
│   └── versions/
│       └── 0001_initial.py      # Full schema migration
│
├── proto/
│   └── library.proto            # Protobuf service + message definitions
│
├── scripts/
│   ├── init_db.sql              # Enum creation (runs at container first start)
│   ├── seed.py                  # Demo data seeder
│   ├── compile_proto.sh         # Generates Python gRPC stubs
│   └── sample_client.py        # Exercises every endpoint via httpx
│
├── tests/
│   └── test_api.py              # Async pytest integration tests
│
├── Dockerfile
├── docker-compose.yml
├── alembic.ini
├── requirements.txt
├── pytest.ini
└── .env.example
```

---

## Database Schema

The schema is implemented exactly as `db_schema.sql` specifies:

| Table | Purpose |
|---|---|
| `authors` | Author master data |
| `books` | Book metadata (title, ISBN, year) |
| `book_authors` | Many-to-many book ↔ author mapping |
| `book_copies` | Individual physical copies with `book_status` enum |
| `members` | Library members |
| `borrow_transactions` | Each borrow/return event with `transaction_status` enum |
| `fines` | Fines attached to overdue transactions |

**Enums**

| Enum | Values |
|---|---|
| `book_status` | `AVAILABLE`, `BORROWED`, `RESERVED`, `LOST` |
| `transaction_status` | `BORROWED`, `RETURNED`, `OVERDUE` |

---

## Quick Start (Docker Compose)

> **Prerequisites**: Docker ≥ 24 and Docker Compose v2

```bash
# 1. Clone / enter the directory
cd library-backend

# 2. Copy environment file
cp .env.example .env

# 3. Build and start everything
#    (Postgres → migrations → API, in order)
docker compose up --build

# API is now live at http://localhost:8000
# Interactive docs: http://localhost:8000/docs
```

To stop:
```bash
docker compose down          # keep data
docker compose down -v       # also delete the postgres volume
```

---

## Local Development Setup

### Prerequisites

- Python 3.12+
- PostgreSQL 14+ running locally (or via Docker)

### Step 1 – Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
```

### Step 2 – Install dependencies

```bash
pip install -r requirements.txt
```

### Step 3 – Start Postgres (Docker, quickest)

```bash
docker run -d \
  --name library_db \
  -e POSTGRES_USER=library_user \
  -e POSTGRES_PASSWORD=library_pass \
  -e POSTGRES_DB=library_db \
  -p 5432:5432 \
  postgres:16-alpine
```

### Step 4 – Create the custom enums

```bash
psql postgresql://library_user:library_pass@localhost:5432/library_db \
     -f scripts/init_db.sql
```

### Step 5 – Set environment variable

```bash
cp .env.example .env
# .env already contains the right localhost URL; edit if your Postgres differs
export DATABASE_URL=postgresql+asyncpg://library_user:library_pass@localhost:5432/library_db
```

---

## Running Database Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Rollback the last migration
alembic downgrade -1

# Auto-generate a new migration after model changes
alembic revision --autogenerate -m "add xyz column"
```

---

## Running the Server

```bash
# Development (live reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Open in browser:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Seeding Demo Data

Creates 4 authors, 5 books (with copies), 3 members, and one overdue loan with a fine:

```bash
python scripts/seed.py
```

---

## Compiling the Proto File

The Protobuf file (`proto/library.proto`) defines the full service interface.
To generate Python stubs (useful for gRPC clients or code generation):

```bash
# Make the script executable once
chmod +x scripts/compile_proto.sh

# Generate stubs into app/proto_gen/
./scripts/compile_proto.sh
```

The generated files (`library_pb2.py` and `library_pb2_grpc.py`) can be used
to build a gRPC gateway on top of the REST service or to auto-generate client SDKs.

---

## API Reference

All routes are under `/api/v1`. Interactive documentation at `/docs`.

### Authors  `GET/POST/PATCH/DELETE /api/v1/authors`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/authors` | List authors (with optional `?search=`) |
| GET | `/authors/{id}` | Get one author |
| POST | `/authors` | Create author |
| PATCH | `/authors/{id}` | Update author name |
| DELETE | `/authors/{id}` | Delete author |

### Books  `GET/POST/PATCH/DELETE /api/v1/books`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/books` | List books (`?search=`, `?author_id=`, `?available_only=true`) |
| GET | `/books/{id}` | Full book detail with authors & copies |
| POST | `/books` | Add book + create copies + link authors |
| PATCH | `/books/{id}` | Update metadata / replace author list |
| DELETE | `/books/{id}` | Delete book (blocked if copies borrowed) |
| GET | `/books/{id}/copies` | List copies (`?status=AVAILABLE`) |
| POST | `/books/{id}/copies` | Add N more copies |
| PATCH | `/books/copies/{copy_id}/status` | Manually set copy status (e.g. LOST) |

### Members  `GET/POST/PATCH/DELETE /api/v1/members`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/members` | List members (`?search=`) |
| GET | `/members/{id}` | Get one member |
| POST | `/members` | Register member |
| PATCH | `/members/{id}` | Update member profile |
| DELETE | `/members/{id}` | Delete member (blocked if active loans) |

### Loans  `/api/v1/loans`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/loans` | **Borrow** a book copy |
| POST | `/loans/{id}/return` | **Return** a book (auto-calculates fine) |
| GET | `/loans` | Full history (`?member_id=`, `?book_id=`, `?status=`, `?overdue_only=true`) |
| GET | `/loans/{id}` | Get single transaction |
| GET | `/loans/borrowed` | All active (unreturned) loans (`?member_id=`) |
| GET | `/loans/due` | All overdue loans |
| GET | `/loans/{id}/fines` | Fines on a specific transaction |
| GET | `/loans/members/{member_id}/fines` | All fines for a member (`?unpaid_only=true`) |
| POST | `/loans/fines/pay` | Mark fines as paid |
| POST | `/loans/mark-overdue` | Admin: batch-transition BORROWED→OVERDUE |
| GET | `/loans/stats` | Dashboard statistics |

---

## Running Tests

```bash
# Make sure Postgres is running and migrations are applied, then:
pytest tests/test_api.py -v

# With coverage
pip install pytest-cov
pytest tests/ --cov=app --cov-report=term-missing
```

---

## Sample Client

Run the sample script to exercise every endpoint against a live server:

```bash
# Server must be running on localhost:8000
python scripts/sample_client.py
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://library_user:library_pass@localhost:5432/library_db` | Full async DB connection URL |
| `SQL_ECHO` | `` (empty) | Set to `1` to log all SQL statements |

---

## Business Rules

- A copy must be `AVAILABLE` to be borrowed. Attempting to borrow a `BORROWED`, `RESERVED`, or `LOST` copy returns **409 Conflict**.
- Returning a copy automatically computes a fine if `return_date > due_date` using `fine_per_day` (default $0.50).
- Deleting a book is blocked while any of its copies are `BORROWED`.
- Deleting a member is blocked while they have active (unreturned) loans.
- The `POST /loans/mark-overdue` endpoint transitions all `BORROWED` transactions past their due date to `OVERDUE` — intended to be called by a scheduler/cron job.


