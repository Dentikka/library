from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models import Library
from app.routers.auth import get_current_active_staff
from app.schemas.library import LibraryCreate, LibraryUpdate, LibraryResponse

router = APIRouter(prefix="/api/v1/libraries", tags=["libraries"])


@router.get("", response_model=List[LibraryResponse])
async def list_libraries(db: AsyncSession = Depends(get_db)):
    """List all libraries (public endpoint)."""
    result = await db.execute(select(Library))
    libraries = result.scalars().all()
    return libraries


@router.get("/{library_id}", response_model=LibraryResponse)
async def get_library(library_id: int, db: AsyncSession = Depends(get_db)):
    """Get library by ID (public endpoint)."""
    result = await db.execute(
        select(Library).where(Library.id == library_id)
    )
    library = result.scalar_one_or_none()
    
    if not library:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Library not found"
        )
    
    return library


@router.post("", response_model=LibraryResponse)
async def create_library(
    library_data: LibraryCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_staff)
):
    """Create new library (staff only)."""
    new_library = Library(**library_data.model_dump())
    db.add(new_library)
    await db.commit()
    await db.refresh(new_library)
    return new_library


@router.put("/{library_id}", response_model=LibraryResponse)
async def update_library(
    library_id: int,
    library_data: LibraryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_staff)
):
    """Update library (staff only)."""
    result = await db.execute(
        select(Library).where(Library.id == library_id)
    )
    library = result.scalar_one_or_none()
    
    if not library:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Library not found"
        )
    
    # Update fields
    update_data = library_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(library, field, value)
    
    await db.commit()
    await db.refresh(library)
    return library


@router.delete("/{library_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_library(
    library_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_staff)
):
    """Delete library (staff only)."""
    result = await db.execute(
        select(Library).where(Library.id == library_id)
    )
    library = result.scalar_one_or_none()
    
    if not library:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Library not found"
        )
    
    await db.delete(library)
    await db.commit()
    return None
