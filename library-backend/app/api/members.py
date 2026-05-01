from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.schemas import MemberCreate, MemberResponse, MemberUpdate
from app.services import members_service

router = APIRouter(prefix="/members", tags=["Members"])


@router.get("/", response_model=dict)
async def list_members(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Filter by name or email"),
    db: AsyncSession = Depends(get_db),
):
    """List all members with optional filtering."""
    total, rows = await members_service.list_members(db, skip, limit, search)
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": [MemberResponse.model_validate(r) for r in rows],
    }


@router.get("/{member_id}", response_model=MemberResponse)
async def get_member(member_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single member by ID."""
    return await members_service.get_or_404(db, member_id)


@router.post("/", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
async def create_member(data: MemberCreate, db: AsyncSession = Depends(get_db)):
    """Create a new member."""
    return await members_service.create_member(db, data)


@router.patch("/{member_id}", response_model=MemberResponse)
async def update_member(
    member_id: int, data: MemberUpdate, db: AsyncSession = Depends(get_db)
):
    """Partially update a member."""
    return await members_service.update_member(db, member_id, data)


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_member(member_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a member if they have no active loans."""
    await members_service.delete_member(db, member_id)
