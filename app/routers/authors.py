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


@router.put("/{author_id}", response_model=AuthorResponse)
async def update_author(
    author_id: int,
    author_data: AuthorCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_staff)
):
    """Update author (staff only)."""
    result = await db.execute(
        select(Author).filter(Author.id == author_id)
    )
    author = result.scalar_one_or_none()
    
    if not author:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Author not found"
        )
    
    # Check if new name already exists (and it's not the same author)
    if author_data.name != author.name:
        existing = await db.execute(
            select(Author).filter(Author.name == author_data.name)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Author with this name already exists"
            )
    
    author.name = author_data.name
    await db.commit()
    await db.refresh(author)
    
    return AuthorResponse(id=author.id, name=author.name)


@router.delete("/{author_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_author(
    author_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_staff)
):
    """Delete author (staff only)."""
    result = await db.execute(
        select(Author).filter(Author.id == author_id)
    )
    author = result.scalar_one_or_none()
    
    if not author:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Author not found"
        )
    
    await db.delete(author)
    await db.commit()
    return None
