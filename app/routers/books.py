from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload
from typing import List, Optional

from app.database import get_db
from app.models import Book, Author, Copy, Library
from app.routers.auth import get_current_active_staff
from app.schemas.book import (
    BookCreate, BookUpdate, BookResponse, BookDetailResponse,
    CopyCreate, CopyUpdate, CopyResponse
)

router = APIRouter(prefix="/api/v1/books", tags=["books"])


@router.get("", response_model=List[BookResponse])
async def list_books(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    author_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """List books with pagination and optional author filter."""
    
    # Build query with counts
    stmt = (
        select(
            Book.id,
            Book.title,
            Book.author_id,
            Book.isbn,
            Book.year,
            Book.description,
            Book.created_at,
            Book.updated_at,
            Author.name.label("author_name"),
            func.count(Copy.id).label("total_count"),
            func.count(Copy.id).filter(Copy.status == "available").label("available_count")
        )
        .join(Author, Book.author_id == Author.id)
        .outerjoin(Copy, Book.id == Copy.book_id)
    )
    
    if author_id:
        stmt = stmt.filter(Book.author_id == author_id)
    
    stmt = (
        stmt.group_by(Book.id, Author.name)
        .offset(skip)
        .limit(limit)
        .order_by(Book.created_at.desc())
    )
    
    result = await db.execute(stmt)
    rows = result.all()
    
    return [
        BookResponse(
            id=row.id,
            title=row.title,
            author_id=row.author_id,
            isbn=row.isbn,
            year=row.year,
            description=row.description,
            created_at=row.created_at,
            updated_at=row.updated_at,
            author_name=row.author_name,
            total_count=row.total_count or 0,
            available_count=row.available_count or 0
        )
        for row in rows
    ]


@router.get("/{book_id}", response_model=BookDetailResponse)
async def get_book(
    book_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get book details with availability by library."""
    
    # Get book with author
    book_result = await db.execute(
        select(Book, Author.name.label("author_name"))
        .join(Author, Book.author_id == Author.id)
        .filter(Book.id == book_id)
    )
    row = book_result.first()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    book, author_name = row
    
    # Get copies with library info
    copies_result = await db.execute(
        select(Copy, Library.name.label("library_name"))
        .join(Library, Copy.library_id == Library.id)
        .filter(Copy.book_id == book_id)
    )
    
    copies_by_library = []
    total_count = 0
    available_count = 0
    
    for copy_row in copies_result:
        copy, library_name = copy_row
        copies_by_library.append({
            "library_id": copy.library_id,
            "library_name": library_name,
            "inventory_number": copy.inventory_number,
            "status": copy.status
        })
        total_count += 1
        if copy.status == "available":
            available_count += 1
    
    return BookDetailResponse(
        id=book.id,
        title=book.title,
        author_id=book.author_id,
        isbn=book.isbn,
        year=book.year,
        description=book.description,
        created_at=book.created_at,
        updated_at=book.updated_at,
        author_name=author_name,
        total_count=total_count,
        available_count=available_count,
        copies_by_library=copies_by_library
    )


@router.post("", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(
    book_data: BookCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_staff)
):
    """Create new book (staff only)."""
    
    # Check if author exists
    author_result = await db.execute(
        select(Author).filter(Author.id == book_data.author_id)
    )
    if not author_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Author not found"
        )
    
    # Create book
    new_book = Book(
        title=book_data.title,
        author_id=book_data.author_id,
        isbn=book_data.isbn,
        year=book_data.year,
        description=book_data.description,
        search_vector=f"{book_data.title}"  # Will be updated with author name later
    )
    
    db.add(new_book)
    await db.commit()
    await db.refresh(new_book)
    
    # Get author name and counts
    result = await db.execute(
        select(
            Book,
            Author.name.label("author_name")
        )
        .join(Author, Book.author_id == Author.id)
        .filter(Book.id == new_book.id)
    )
    book_row = result.first()
    
    return BookResponse(
        id=book_row.Book.id,
        title=book_row.Book.title,
        author_id=book_row.Book.author_id,
        isbn=book_row.Book.isbn,
        year=book_row.Book.year,
        description=book_row.Book.description,
        created_at=book_row.Book.created_at,
        updated_at=book_row.Book.updated_at,
        author_name=book_row.author_name,
        total_count=0,
        available_count=0
    )


@router.put("/{book_id}", response_model=BookResponse)
async def update_book(
    book_id: int,
    book_data: BookUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_staff)
):
    """Update book (staff only)."""
    
    # Get book
    result = await db.execute(
        select(Book).filter(Book.id == book_id)
    )
    book = result.scalar_one_or_none()
    
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    # Update fields
    update_data = book_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(book, field, value)
    
    await db.commit()
    await db.refresh(book)
    
    # Get full response
    return await get_book(book_id, db)


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(
    book_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_staff)
):
    """Delete book (staff only)."""
    
    result = await db.execute(
        select(Book).filter(Book.id == book_id)
    )
    book = result.scalar_one_or_none()
    
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    await db.delete(book)
    await db.commit()
    return None


# Copy management endpoints

@router.get("/{book_id}/copies", response_model=List[CopyResponse])
async def get_book_copies(
    book_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get all copies of a book."""
    
    result = await db.execute(
        select(
            Copy,
            Library.name.label("library_name"),
            Book.title.label("book_title")
        )
        .join(Library, Copy.library_id == Library.id)
        .join(Book, Copy.book_id == Book.id)
        .filter(Copy.book_id == book_id)
    )
    
    return [
        CopyResponse(
            id=row.Copy.id,
            book_id=row.Copy.book_id,
            library_id=row.Copy.library_id,
            inventory_number=row.Copy.inventory_number,
            status=row.Copy.status,
            created_at=row.Copy.created_at,
            library_name=row.library_name,
            book_title=row.book_title
        )
        for row in result
    ]


@router.post("/{book_id}/copies", response_model=CopyResponse, status_code=status.HTTP_201_CREATED)
async def create_copy(
    book_id: int,
    copy_data: CopyCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_staff)
):
    """Add a copy of a book (staff only)."""
    
    # Verify book exists
    book_result = await db.execute(
        select(Book).filter(Book.id == book_id)
    )
    if not book_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    # Verify library exists
    library_result = await db.execute(
        select(Library).filter(Library.id == copy_data.library_id)
    )
    library = library_result.scalar_one_or_none()
    if not library:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Library not found"
        )
    
    # Create copy
    new_copy = Copy(
        book_id=book_id,
        library_id=copy_data.library_id,
        inventory_number=copy_data.inventory_number,
        status=copy_data.status
    )
    
    db.add(new_copy)
    await db.commit()
    await db.refresh(new_copy)
    
    # Get book title
    book_result = await db.execute(
        select(Book.title).filter(Book.id == book_id)
    )
    book_title = book_result.scalar()
    
    return CopyResponse(
        id=new_copy.id,
        book_id=new_copy.book_id,
        library_id=new_copy.library_id,
        inventory_number=new_copy.inventory_number,
        status=new_copy.status,
        created_at=new_copy.created_at,
        library_name=library.name,
        book_title=book_title
    )


@router.put("/copies/{copy_id}", response_model=CopyResponse)
async def update_copy(
    copy_id: int,
    copy_data: CopyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_staff)
):
    """Update copy (staff only)."""
    
    result = await db.execute(
        select(Copy).filter(Copy.id == copy_id)
    )
    copy = result.scalar_one_or_none()
    
    if not copy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Copy not found"
        )
    
    # Update fields
    update_data = copy_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(copy, field, value)
    
    await db.commit()
    await db.refresh(copy)
    
    # Get full response
    result = await db.execute(
        select(
            Copy,
            Library.name.label("library_name"),
            Book.title.label("book_title")
        )
        .join(Library, Copy.library_id == Library.id)
        .join(Book, Copy.book_id == Book.id)
        .filter(Copy.id == copy_id)
    )
    row = result.first()
    
    return CopyResponse(
        id=row.Copy.id,
        book_id=row.Copy.book_id,
        library_id=row.Copy.library_id,
        inventory_number=row.Copy.inventory_number,
        status=row.Copy.status,
        created_at=row.Copy.created_at,
        library_name=row.library_name,
        book_title=row.book_title
    )


@router.delete("/copies/{copy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_copy(
    copy_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_staff)
):
    """Delete copy (staff only)."""
    
    result = await db.execute(
        select(Copy).filter(Copy.id == copy_id)
    )
    copy = result.scalar_one_or_none()
    
    if not copy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Copy not found"
        )
    
    await db.delete(copy)
    await db.commit()
    return None
