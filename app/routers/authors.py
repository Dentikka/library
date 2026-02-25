from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models import Author
from app.routers.auth import get_current_active_staff
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/authors", tags=["authors"])


class AuthorResponse(BaseModel):
    id: int
    name: str
    
    class Config:
        from_attributes = True


class AuthorCreate(BaseModel):
    name: str


@router.get("", response_model=List[AuthorResponse])
async def list_authors(
    db: AsyncSession = Depends(get_db)
):
    """List all authors."""
    result = await db.execute(select(Author).order_by(Author.name))
    authors = result.scalars().all()
    return [AuthorResponse(id=a.id, name=a.name) for a in authors]


@router.post("", response_model=AuthorResponse, status_code=status.HTTP_201_CREATED)
async def create_author(
    author_data: AuthorCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_staff)
):
    """Create new author (staff only)."""
    # Check if author already exists
    result = await db.execute(
        select(Author).filter(Author.name == author_data.name)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Author already exists"
        )
    
    new_author = Author(name=author_data.name)
    db.add(new_author)
    await db.commit()
    await db.refresh(new_author)
    
    return AuthorResponse(id=new_author.id, name=new_author.name)
