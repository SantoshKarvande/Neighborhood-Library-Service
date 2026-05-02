# 📚 Neighborhood Library Service — Backend

Python **FastAPI** backend for the Neighborhood Library Service. Exposes a REST API supporting both **JSON** and **Protocol Buffers (Protobuf)** encoding, backed by a **PostgreSQL** database managed via **Alembic** migrations.

---

## 🧰 Tech Stack

| Technology | Purpose |
|---|---|
| Python 3.13 | Runtime |
| FastAPI | Web framework |
| Uvicorn + uvloop | ASGI server |
| SQLAlchemy 2.x (async) | ORM |
| asyncpg | Async PostgreSQL driver |
| Alembic | Database migrations |
| Pydantic v2 | Request/response validation |
| protobuf + grpcio-tools | Protocol Buffers support |
| pytest + httpx | Testing |
| Docker + Docker Compose | Containerisation |

---

## 🗂️ Project Structure

```
library-backend/
├── app/
│   ├── api/                     ← Route handlers
│   │   ├── authors.py
│   │   ├── books.py
│   │   ├── loans.py
│   │   └── members.py
│   ├── core/
│   │   └── database.py          ← SQLAlchemy async engine & session
│   ├── middleware/
│   │   └── protobuf.py          ← Protobuf request/response middleware
│   ├── models/
│   │   └── models.py            ← SQLAlchemy ORM models
│   ├── proto_gen/
│   │   ├── library_pb2.py       ← Auto-generated Protobuf Python classes
│   │   ├── library_pb2.pyi      ← Type stubs
│   │   └── serializer.py        ← Protobuf ↔ dict serializers
│   ├── schemas/
│   │   └── schemas.py           ← Pydantic schemas
│   ├── services/
│   │   ├── authors_service.py
│   │   ├── books_service.py
│   │   ├── loans_service.py
│   │   └── members_service.py
│   └── main.py                  ← FastAPI app entry point
├── migrations/                  ← Alembic migrations
│   ├── versions/
│   │   └── 0001_initial.py      ← Initial schema (tables + ENUMs)
│   ├── env.py                   ← Alembic async environment
│   └── script.py.mako
├── proto/
│   └── library.proto            ← Protobuf schema definition
├── scripts/
│   ├── init_db.sql              ← Drops/recreates DB + user + grants
│   ├── compile_proto.sh         ← Regenerates proto_gen/ from .proto
│   ├── seed.py                  ← Seeds sample data
│   ├── sample_client.py         ← CLI JSON test client
│   └── proto_client.py          ← CLI Protobuf test client
├── tests/
│   └── test_api.py
├── Dockerfile                   ← Multi-stage production image
├── .dockerignore
├── .env.example
├── alembic.ini
├── pytest.ini
└── requirements.txt
```

---

## ✅ Prerequisites (Local Development)

| Tool | Version |
|---|---|
| Python | 3.13+ |
| Docker Desktop | Latest |
| protoc | 3.x (only if modifying .proto files) |

> To run via Docker only, Docker Desktop is the sole requirement.

---

## 🐳 Run with Docker (Recommended)

Use the **root-level** `docker-compose.yml` from the project root to start the entire stack (DB + migrations + backend + frontend) together:

```bash
# From the project root — Neighborhood-Library-Service/
docker-compose up --build
```

To run the backend service alone with its own database:

```bash
cd library-backend
docker-compose up --build
```

**Services started:**

| Service | URL |
|---|---|
| Backend API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Health check | http://localhost:8000/health |
| Proto schema | http://localhost:8000/proto-schema |

---

## 🛠️ Local Development Setup

### 1. Start PostgreSQL

```bash
cd library-backend
docker-compose up -d db
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Update `.env`:

```env
# For local development (outside Docker)
DATABASE_URL=postgresql+asyncpg://library_user:library_pass@localhost:5432/library_db
```

### 5. Run database migrations

```bash
alembic upgrade head
```

### 6. Start the development server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🗄️ Database

### Credentials

| Setting | Value |
|---|---|
| Database | `library_db` |
| User | `library_user` |
| Password | `library_pass` |
| Port | `5432` |

The database is initialised by `scripts/init_db.sql` which runs automatically on first container start. It:
- Drops and recreates `library_db` and `library_user` on every fresh volume start
- Grants full `READ / WRITE / EXECUTE` permissions on all tables, sequences, and functions to `library_user`

### Migration commands

```bash
# Apply all pending migrations
alembic upgrade head

# Create a new migration after model changes
alembic revision --autogenerate -m "describe your change"

# Rollback one step
alembic downgrade -1

# Check current state
alembic current

# View history
alembic history
```

### Seed sample data

```bash
python scripts/seed.py
```

---

## 🔌 API Endpoints

All endpoints support **JSON** (default) and **Protocol Buffers**.

To use Protobuf encoding, set request headers:
```
Content-Type: application/x-protobuf
Accept:       application/x-protobuf
```

| Resource | Base Path | Operations |
|---|---|---|
| Authors | `/api/v1/authors` | GET, POST, GET /{id}, PUT /{id}, DELETE /{id} |
| Books | `/api/v1/books` | GET, POST, GET /{id}, PUT /{id}, DELETE /{id} |
| Members | `/api/v1/members` | GET, POST, GET /{id}, PUT /{id}, DELETE /{id} |
| Loans | `/api/v1/loans` | GET, POST, GET /{id}, PUT /{id}, DELETE /{id} |

Full interactive docs: **http://localhost:8000/docs**

---

## 🔄 Protocol Buffers

The schema is defined in `proto/library.proto`.

If you modify the `.proto` file, regenerate the Python stubs:

```bash
chmod +x scripts/compile_proto.sh
./scripts/compile_proto.sh
```

This regenerates `app/proto_gen/library_pb2.py` and `library_pb2.pyi`.

> Keep `proto/library.proto` in sync with `library-frontend/public/proto/library.proto`.

---

## 🧪 Running Tests

```bash
source .venv/bin/activate

pytest                     # all tests
pytest -v                  # verbose
pytest tests/test_api.py   # specific file
```

---

## 🌍 Environment Variables

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL async connection string | `postgresql+asyncpg://library_user:library_pass@db:5432/library_db` |
| `SQL_ECHO` | Set to `1` to log all SQL queries | `` (disabled) |

> Inside Docker Compose, use `@db:5432` as the host. For local development outside Docker, use `@localhost:5432`.

---

## 🐳 Docker Reference

```bash
# Build and start
docker-compose up --build

# Start in background
docker-compose up -d

# Stop services
docker-compose down

# Full reset — wipe DB volume and restart clean
docker-compose down -v --remove-orphans
docker-compose up --build

# View logs
docker-compose logs -f
```
