from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from app.api import authors, books, loans, members
from app.core.database import engine
from app.middleware.protobuf import ProtobufMiddleware
from app.models.models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="Neighborhood Library Service",
    description=(
        "REST API supporting both **JSON** and **Protocol Buffers** encoding.\n\n"
        "Use `Content-Type: application/x-protobuf` to send Protobuf bodies.\n"
        "Use `Accept: application/x-protobuf` to receive Protobuf responses."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

# ─── Middleware (order matters: Protobuf before CORS) ─────────────────────────
app.add_middleware(ProtobufMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────
PREFIX = "/api/v1"
app.include_router(authors.router, prefix=PREFIX)
app.include_router(books.router,   prefix=PREFIX)
app.include_router(members.router, prefix=PREFIX)
app.include_router(loans.router,   prefix=PREFIX)


# ─── Health & schema discovery ────────────────────────────────────────────────

@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "ok",
        "service": "Neighborhood Library API",
        "version": "2.0.0",
        "encodings": ["application/json", "application/x-protobuf"],
        "proto_schema": "/proto-schema",
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}


@app.get("/proto-schema", tags=["Schema"], response_class=PlainTextResponse)
async def proto_schema():
    """Returns the raw .proto file so clients can inspect the message schema."""
    proto_file = Path("proto/library.proto")
    if proto_file.exists():
        return proto_file.read_text()
    return "Proto file not found. Run from the project root directory."

