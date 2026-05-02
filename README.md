# 📚 Neighborhood Library Service

A full-stack **Library Management System** for managing books, authors, members, and loan transactions. Built with a **Python FastAPI** backend and a **Next.js (TypeScript)** frontend, communicating over both **JSON** and **Protocol Buffers (Protobuf)**. The entire stack runs with a single Docker Compose command.

🔗 **GitHub:** https://github.com/SantoshKarvande/Neighborhood-Library-Service

---

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, TypeScript, App Router |
| Backend | Python 3.13, FastAPI, Uvicorn |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy 2.x (async) |
| Migrations | Alembic |
| Serialization | Protocol Buffers (protobuf3) + JSON |
| Testing (BE) | pytest |
| Testing (FE) | Vitest |
| Containerization | Docker, Docker Compose |

---

## 🗂️ Project Structure

```
Neighborhood-Library-Service/
├── docker-compose.yml               ← Orchestrates all services
├── .gitignore
├── README.md
│
├── library-backend/                 ← Python FastAPI backend
│   ├── app/
│   │   ├── api/                     ← Route handlers (authors, books, members, loans)
│   │   ├── core/database.py         ← SQLAlchemy async engine
│   │   ├── middleware/protobuf.py   ← Protobuf request/response middleware
│   │   ├── models/models.py         ← SQLAlchemy ORM models
│   │   ├── proto_gen/               ← Auto-generated Protobuf Python classes
│   │   ├── schemas/schemas.py       ← Pydantic schemas
│   │   ├── services/                ← Business logic per resource
│   │   └── main.py                  ← FastAPI app entry point
│   ├── migrations/                  ← Alembic migration scripts
│   │   └── versions/0001_initial.py
│   ├── proto/library.proto          ← Protobuf schema definition
│   ├── scripts/
│   │   ├── init_db.sql              ← DB initialisation (drop/recreate + grants)
│   │   ├── seed.py                  ← Sample data seeder
│   │   ├── compile_proto.sh         ← Regenerate proto_gen/ from .proto
│   │   ├── sample_client.py         ← CLI JSON test client
│   │   └── proto_client.py          ← CLI Protobuf test client
│   ├── tests/test_api.py
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   └── .env.example
│
└── library-frontend/                ← Next.js TypeScript frontend
    ├── app/                         ← Next.js App Router pages
    ├── lib/
    │   ├── api.ts                   ← API fetch wrappers
    │   └── protobuf.ts              ← Protobuf encode/decode helpers
    ├── public/proto/                ← .proto files served to browser
    ├── tests/
    ├── Dockerfile
    ├── package.json
    └── .env.example
```

---

## ✅ Prerequisites

| Tool | Version | Install |
|---|---|---|
| Docker Desktop | Latest | https://www.docker.com/products/docker-desktop |
| Git | Latest | https://git-scm.com/ |

> Docker Desktop includes Docker Compose v2. No other tools are required to build and run the project.

---

## 🚀 Quick Start (Docker — Recommended)

This is the fastest way to get the entire stack running with a single command.

### 1. Clone the repository

```bash
git clone https://github.com/SantoshKarvande/Neighborhood-Library-Service.git
cd Neighborhood-Library-Service
```

### 2. Start Docker Desktop

Make sure Docker Desktop is running on your machine before proceeding.

```bash
# Verify Docker is running
docker info
```

### 3. Free up required ports

The project uses ports `3000`, `8000`, and `5432`. If any are already in use:

```bash
kill -9 $(lsof -ti :3000) $(lsof -ti :8000) $(lsof -ti :5432) 2>/dev/null || true
```

### 4. Build and start all services

```bash
docker-compose up --build
```

This single command will:
- Start **PostgreSQL** and initialise the database (`library_db`) with user `library_user`
- Run **Alembic migrations** to create all tables
- Start the **FastAPI backend** on port `8000`
- Start the **Next.js frontend** on port `3000`

### 5. Open the application

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Swagger UI (API docs) | http://localhost:8000/docs |
| ReDoc (API docs) | http://localhost:8000/redoc |
| Health check | http://localhost:8000/health |

---

## 🔄 Common Docker Commands

```bash
# Start all services (after first build)
docker-compose up

# Start in background (detached mode)
docker-compose up -d

# Rebuild images and start (after code changes)
docker-compose up --build

# Stop all services
docker-compose down

# Full reset — stop, remove containers, wipe database volume
docker-compose down -v --remove-orphans

# View logs for all services
docker-compose logs -f

# View logs for a specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db
docker-compose logs -f migrate
```

---

## 🔌 API Overview

All endpoints support both **JSON** and **Protocol Buffers**:
- JSON: default — no special headers needed
- Protobuf: set `Content-Type: application/x-protobuf` and `Accept: application/x-protobuf`

| Resource | Base Path | Methods |
|---|---|---|
| Authors | `/api/v1/authors` | GET (list), POST, GET /{id}, PUT /{id}, DELETE /{id} |
| Books | `/api/v1/books` | GET (list), POST, GET /{id}, PUT /{id}, DELETE /{id} |
| Members | `/api/v1/members` | GET (list), POST, GET /{id}, PUT /{id}, DELETE /{id} |
| Loans | `/api/v1/loans` | GET (list), POST, GET /{id}, PUT /{id}, DELETE /{id} |

Full interactive API documentation is available at **http://localhost:8000/docs** when the server is running.

---

## 🛠️ Local Development Setup (Without Docker)

Use this if you want to run the backend or frontend locally outside containers.

### Backend

```bash
cd library-backend

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate          # macOS / Linux
# .venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and set DATABASE_URL to point to your local PostgreSQL

# Run migrations
alembic upgrade head

# Start the development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd library-frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local
# Edit .env.local and set NEXT_PUBLIC_API_URL=http://localhost:8000

# Start the development server
npm run dev
```

---

## 🧪 Running Tests

### Backend tests (pytest)

```bash
cd library-backend
source .venv/bin/activate

pytest                     # run all tests
pytest -v                  # verbose output
pytest tests/test_api.py   # specific file
```

### Frontend tests (Vitest)

```bash
cd library-frontend

npm run test               # run all tests once
npm run test:watch         # run in watch mode
```

---

## 🗄️ Database Management

```bash
cd library-backend
source .venv/bin/activate

# Apply all pending migrations
alembic upgrade head

# Create a new migration after model changes
alembic revision --autogenerate -m "your description"

# Rollback one migration
alembic downgrade -1

# Check current migration state
alembic current

# View full migration history
alembic history

# Seed the database with sample data
python scripts/seed.py
```

---

## 🔄 Protobuf Schema

The Protobuf schema is defined in `library-backend/proto/library.proto` and mirrored at `library-frontend/public/proto/library.proto`. Both files must stay in sync.

If you modify the `.proto` schema, regenerate the Python stubs:

```bash
cd library-backend
chmod +x scripts/compile_proto.sh
./scripts/compile_proto.sh
```

The frontend loads `.proto` files dynamically at runtime via `protobufjs` — no frontend compile step is needed.

---

## 🌍 Environment Variables

### Backend (`library-backend/.env`)

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL async connection string | `postgresql+asyncpg://library_user:library_pass@db:5432/library_db` |
| `SQL_ECHO` | Set to `1` to log all SQL queries | `` (disabled) |

### Frontend (`library-frontend/.env.local`)

| Variable | Description | Default |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | Backend API base URL | `http://localhost:8000` |

---

## 📄 License

This project is licensed under the MIT License.
