# 📚 Library Management System

A full-stack Library Management System built with a **Python FastAPI** backend and a **Next.js (TypeScript)** frontend. The backend exposes a REST API with **Protocol Buffers (Protobuf)** serialization, backed by a **PostgreSQL** database managed via **Alembic** migrations.

---

## 🗂️ Project Structure

```
Library_Git/
├── README.md                        ← You are here (root README)
│
├── library-backend/                 ← Python FastAPI backend
│   ├── app/
│   │   ├── api/                     ← Route handlers (books, authors, members, loans)
│   │   │   ├── authors.py
│   │   │   ├── books.py
│   │   │   ├── loans.py
│   │   │   └── members.py
│   │   ├── core/
│   │   │   └── database.py          ← SQLAlchemy engine & session setup
│   │   ├── middleware/
│   │   │   └── protobuf.py          ← Protobuf request/response middleware
│   │   ├── models/
│   │   │   └── models.py            ← SQLAlchemy ORM models
│   │   ├── proto_gen/
│   │   │   ├── library_pb2.py       ← Auto-generated Protobuf Python classes
│   │   │   ├── library_pb2.pyi      ← Type stubs for pb2
│   │   │   └── serializer.py        ← Protobuf ↔ Python dict serializers
│   │   ├── schemas/
│   │   │   └── schemas.py           ← Pydantic request/response schemas
│   │   ├── services/
│   │   │   ├── authors_service.py   ← Business logic: authors
│   │   │   ├── books_service.py     ← Business logic: books
│   │   │   ├── loans_service.py     ← Business logic: loans
│   │   │   └── members_service.py   ← Business logic: members
│   │   └── main.py                  ← FastAPI app entry point
│   ├── migrations/                  ← Alembic migration scripts
│   │   ├── versions/
│   │   │   └── 0001_initial.py      ← Initial DB schema migration
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── proto/
│   │   └── library.proto            ← Protobuf schema definition
│   ├── scripts/
│   │   ├── compile_proto.sh         ← Script to regenerate proto_gen/ from .proto
│   │   ├── init_db.sql              ← Optional raw SQL DB init
│   │   ├── proto_client.py          ← CLI test client using Protobuf
│   │   ├── sample_client.py         ← CLI test client using JSON
│   │   └── seed.py                  ← Database seed script
│   ├── tests/
│   │   └── test_api.py              ← pytest API test suite
│   ├── .env.example                 ← Environment variable template
│   ├── alembic.ini                  ← Alembic configuration
│   ├── docker-compose.yml           ← PostgreSQL via Docker
│   ├── pytest.ini                   ← pytest configuration
│   └── requirements.txt             ← Python dependencies
│
└── library-frontend/                ← Next.js TypeScript frontend
    ├── app/
    │   ├── globals.css              ← Global styles
    │   ├── layout.tsx               ← Root layout component
    │   └── page.tsx                 ← Home page
    ├── lib/
    │   ├── api.ts                   ← API client (fetch wrappers)
    │   └── protobuf.ts              ← Protobuf encode/decode helpers
    ├── public/
    │   └── proto/
    │       ├── library.proto        ← Protobuf schema (served to browser)
    │       └── google/protobuf/
    │           └── timestamp.proto  ← Google well-known type
    ├── tests/
    │   ├── protobuf-client.test.ts  ← Vitest tests for Protobuf client
    │   └── setup.ts                 ← Vitest setup
    ├── .env.example                 ← Environment variable template
    ├── .eslintrc.json               ← ESLint configuration
    ├── next.config.mjs              ← Next.js configuration
    ├── package.json                 ← Node.js dependencies & scripts
    ├── tsconfig.json                ← TypeScript configuration
    └── vitest.config.ts             ← Vitest test configuration
```

---

## 🧰 Tech Stack

| Layer       | Technology                                    |
|-------------|-----------------------------------------------|
| Frontend    | Next.js 14+, TypeScript, App Router           |
| Backend     | Python 3.13, FastAPI, Uvicorn                 |
| Database    | PostgreSQL 15+                                |
| ORM         | SQLAlchemy 2.x                                |
| Migrations  | Alembic                                       |
| Serialization | Protocol Buffers (protobuf3)               |
| Testing (BE)| pytest                                        |
| Testing (FE)| Vitest                                        |
| Containerization | Docker, Docker Compose                   |

---

## ✅ Prerequisites

Make sure the following are installed on your machine:

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.13+ | https://www.python.org/downloads/ |
| Node.js | 18+ | https://nodejs.org/ |
| npm | 9+ | Bundled with Node.js |
| Docker | Latest | https://www.docker.com/products/docker-desktop |
| Docker Compose | v2+ | Bundled with Docker Desktop |
| protoc | 3.x | https://grpc.io/docs/protoc-installation/ |
| grpc_tools | (Python) | Installed via requirements.txt |
| git | Latest | https://git-scm.com/ |

---

## 🚀 Getting Started (Full Setup)

### 1. Clone the Repository

```bash
git clone https://github.com/<your-username>/Library_Git.git
cd Library_Git
```

---

## 🐍 Backend Setup (`library-backend`)

### 2. Start PostgreSQL with Docker

```bash
cd library-backend
docker-compose up -d
```

This starts a PostgreSQL container. Verify it is running:

```bash
docker ps
```

### 3. Create and Activate a Python Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# OR
.venv\Scripts\activate           # Windows PowerShell
```

### 4. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

```bash
cp .env.example .env
```

Open `.env` and update the values as needed:

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/library_db
```

> The default values in `.env.example` are pre-configured to work with `docker-compose.yml` out of the box.

### 6. Run Database Migrations

```bash
alembic upgrade head
```

This creates all required tables in the PostgreSQL database.

### 7. (Optional) Seed the Database

```bash
python scripts/seed.py
```

This populates the database with sample authors, books, and members.

### 8. Recompile Protobuf Files (only if `.proto` schema changes)

```bash
chmod +x scripts/compile_proto.sh
./scripts/compile_proto.sh
```

This regenerates `app/proto_gen/library_pb2.py` and `library_pb2.pyi` from `proto/library.proto`.

### 9. Run the Backend Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API Base:** `http://localhost:8000`
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

---

## 🌐 Frontend Setup (`library-frontend`)

### 10. Install Node.js Dependencies

```bash
cd ../library-frontend
npm install
```

### 11. Configure Environment Variables

```bash
cp .env.example .env.local
```

Open `.env.local` and update:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 12. Run the Frontend Development Server

```bash
npm run dev
```

The frontend will be available at: **`http://localhost:3000`**

---

## 🏗️ Build Instructions

### Backend (Production)

The backend runs directly with Uvicorn. For production use a process manager:

```bash
# Install gunicorn (production WSGI/ASGI server)
pip install gunicorn

# Run with multiple workers
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Frontend (Production Build)

```bash
cd library-frontend
npm run build
```

This generates an optimized production build in the `.next/` folder.

To serve the production build:

```bash
npm run start
```

---

## 🧪 Running Tests

### Backend Tests (pytest)

```bash
cd library-backend
source .venv/bin/activate

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run a specific test file
pytest tests/test_api.py
```

Test configuration is in `pytest.ini`.

### Frontend Tests (Vitest)

```bash
cd library-frontend

# Run all tests
npm run test

# Run tests in watch mode
npm run test -- --watch
```

Test configuration is in `vitest.config.ts`.

---

## 🔌 API Overview

The backend exposes the following resource endpoints. All endpoints support both **JSON** and **Protocol Buffers** (set `Content-Type: application/x-protobuf` and `Accept: application/x-protobuf`).

| Resource | Base Path    | Operations                        |
|----------|--------------|-----------------------------------|
| Authors  | `/authors`   | GET (list), POST, GET (by id), PUT, DELETE |
| Books    | `/books`     | GET (list), POST, GET (by id), PUT, DELETE |
| Members  | `/members`   | GET (list), POST, GET (by id), PUT, DELETE |
| Loans    | `/loans`     | GET (list), POST, GET (by id), PUT, DELETE |

Full API documentation is auto-generated at **`http://localhost:8000/docs`** when the server is running.

---

## 🔄 Protocol Buffers

The Protobuf schema is defined in:
- **Backend:** `library-backend/proto/library.proto`
- **Frontend:** `library-frontend/public/proto/library.proto`

Both files should remain in sync. If you modify the `.proto` file:

**Backend — regenerate Python stubs:**
```bash
cd library-backend
./scripts/compile_proto.sh
```

**Frontend** — the browser loads `.proto` files dynamically via `lib/protobuf.ts` using `protobufjs`, so no compile step is needed on the frontend.

---

## 🗄️ Database Migrations

Migrations are managed with Alembic.

```bash
cd library-backend
source .venv/bin/activate

# Apply all pending migrations
alembic upgrade head

# Create a new migration (after changing models)
alembic revision --autogenerate -m "describe your change"

# Downgrade one step
alembic downgrade -1

# View current migration state
alembic current

# View migration history
alembic history
```

---

## 🐳 Docker Reference

```bash
cd library-backend

# Start PostgreSQL container
docker-compose up -d

# Stop the container
docker-compose down

# Stop and remove volumes (wipes database data)
docker-compose down -v

# View container logs
docker-compose logs -f
```

---

## 🛠️ Useful Scripts

| Script | Location | Description |
|--------|----------|-------------|
| `compile_proto.sh` | `library-backend/scripts/` | Recompiles `.proto` → Python `pb2` files |
| `seed.py` | `library-backend/scripts/` | Seeds the database with sample data |
| `init_db.sql` | `library-backend/scripts/` | Raw SQL to initialize DB schema manually |
| `sample_client.py` | `library-backend/scripts/` | CLI client using JSON API |
| `proto_client.py` | `library-backend/scripts/` | CLI client using Protobuf API |

Run scripts from within the `library-backend/` directory with the virtual environment activated.

---

## 🌍 Environment Variables Reference

### Backend (`.env`)

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:password@localhost:5432/library_db` |

### Frontend (`.env.local`)

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API base URL | `http://localhost:8000` |

---

## 📁 Files Excluded from Git

The following are excluded via `.gitignore` and should **never** be committed:

- `.env` — contains secrets/credentials
- `.venv/`, `.venv_old/` — Python virtual environment directories
- `__pycache__/`, `*.pyc` — Python bytecode
- `.next/` — Next.js build output
- `node_modules/` — Node.js packages
- `*.bk`, `*.bk1`, `*.updated` — Backup/temporary editor files
- `.DS_Store` — macOS metadata files

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes and add tests
4. Run the test suites to ensure nothing is broken
5. Commit your changes: `git commit -m "feat: add your feature"`
6. Push to your branch: `git push origin feature/your-feature-name`
7. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License.
