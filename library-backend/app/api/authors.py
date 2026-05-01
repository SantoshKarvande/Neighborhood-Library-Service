from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.schemas import AuthorCreate, AuthorResponse, AuthorUpdate
from app.services import authors_service

router = APIRouter(prefix="/authors", tags=["Authors"])


@router.get("/", response_model=dict)
async def list_authors(
    skip:   int            = Query(0, ge=0),
    limit:  int            = Query(20, ge=1, le=100),
    search: Optional[str]  = Query(None, description="Filter by name"),
    db: AsyncSession       = Depends(get_db),
):
    """List all authors with optional name search."""
    total, rows = await authors_service.list_authors(db, skip, limit, search)
    return {"total": total, "skip": skip, "limit": limit,
            "items": [AuthorResponse.model_validate(r) for r in rows]}


@router.get("/{author_id}", response_model=AuthorResponse)
async def get_author(author_id: int, db: AsyncSession = Depends(get_db)):
    return await authors_service.get_or_404(db, author_id)


@router.post("/", response_model=AuthorResponse, status_code=status.HTTP_201_CREATED)
async def create_author(data: AuthorCreate, db: AsyncSession = Depends(get_db)):
    """Create a new author record."""
    return await authors_service.create_author(db, data)


@router.patch("/{author_id}", response_model=AuthorResponse)
async def update_author(
    author_id: int, data: AuthorUpdate, db: AsyncSession = Depends(get_db)
):
    """Partially update an author."""
    return await authors_service.update_author(db, author_id, data)


@router.delete("/{author_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_author(author_id: int, db: AsyncSession = Depends(get_db)):
    await authors_service.delete_author(db, author_id)

