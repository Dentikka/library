from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from typing import List, Optional

from app.database import get_db
from app.models import Book, Author, Copy, Library
from app.schemas.search import SearchResponse, SearchResult, SearchSuggestions

router = APIRouter(prefix="/api/v1/search", tags=["search"])


@router.get("", response_model=SearchResponse)
async def search_books(
    q: str = Query(..., min_length=1, description="Search query"),
    library_id: Optional[int] = Query(None, description="Filter by library ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Search books by title or author name.
    Supports filtering by library (to show only books available there).
    """
    query = q.strip()
    
    # Build base query with joins
    stmt = (
        select(
            Book.id,
            Book.title,
            Author.name.label("author_name"),
            Book.year,
            func.count(Copy.id).label("total_count"),
            func.count(Copy.id).filter(Copy.status == "available").label("available_count")
        )
        .join(Author, Book.author_id == Author.id)
        .outerjoin(Copy, Book.id == Copy.book_id)
    )
    
    # Apply library filter if specified
    if library_id:
        stmt = stmt.filter(Copy.library_id == library_id)
    
    # Search in title or author name (case-insensitive)
    search_pattern = f"%{query}%"
    stmt = stmt.filter(
        or_(
            Book.title.ilike(search_pattern),
            Author.name.ilike(search_pattern)
        )
    )
    
    # Group by book and author
    stmt = stmt.group_by(Book.id, Book.title, Author.name, Book.year)
    
    # Order by relevance (title match first, then author match)
    stmt = stmt.order_by(
        Book.title.ilike(f"%{query}%").desc(),
        Author.name.ilike(f"%{query}%").desc(),
        Book.title
    )
    
    result = await db.execute(stmt)
    rows = result.all()
    
    # Format results
    results = [
        SearchResult(
            id=row.id,
            title=row.title,
            author_name=row.author_name,
            year=row.year,
            available_count=row.available_count or 0,
            total_count=row.total_count or 0
        )
        for row in rows
    ]
    
    return SearchResponse(
        query=query,
        total=len(results),
        results=results
    )


@router.get("/suggestions", response_model=SearchSuggestions)
async def get_suggestions(
    q: str = Query(..., min_length=1, description="Search query prefix"),
    limit: int = Query(5, ge=1, le=10),
    db: AsyncSession = Depends(get_db)
):
    """
    Get search suggestions (autocomplete).
    Returns matching book titles and author names.
    """
    query = q.strip()
    search_pattern = f"%{query}%"
    
    # Get matching book titles
    book_stmt = (
        select(Book.title)
        .filter(Book.title.ilike(search_pattern))
        .limit(limit)
    )
    
    # Get matching author names
    author_stmt = (
        select(Author.name)
        .filter(Author.name.ilike(search_pattern))
        .limit(limit)
    )
    
    book_result = await db.execute(book_stmt)
    author_result = await db.execute(author_stmt)
    
    suggestions = []
    
    # Add book titles
    for row in book_result:
        suggestions.append(f"📚 {row.title}")
    
    # Add author names
    for row in author_result:
        suggestions.append(f"✍️ {row.name}")
    
    # Remove duplicates and limit
    seen = set()
    unique_suggestions = []
    for s in suggestions:
        if s not in seen:
            seen.add(s)
            unique_suggestions.append(s)
        if len(unique_suggestions) >= limit:
            break
    
    return SearchSuggestions(
        query=query,
        suggestions=unique_suggestions
    )


@router.get("/advanced", response_model=SearchResponse)
async def advanced_search(
    title: Optional[str] = Query(None, description="Search in title"),
    author: Optional[str] = Query(None, description="Search in author name"),
    year_from: Optional[int] = Query(None, description="Year from"),
    year_to: Optional[int] = Query(None, description="Year to"),
    library_id: Optional[int] = Query(None, description="Filter by library"),
    available_only: bool = Query(False, description="Only available books"),
    db: AsyncSession = Depends(get_db)
):
    """
    Advanced search with multiple filters.
    """
    # Build base query
    stmt = (
        select(
            Book.id,
            Book.title,
            Author.name.label("author_name"),
            Book.year,
            func.count(Copy.id).label("total_count"),
            func.count(Copy.id).filter(Copy.status == "available").label("available_count")
        )
        .join(Author, Book.author_id == Author.id)
        .outerjoin(Copy, Book.id == Copy.book_id)
    )
    
    # Apply filters
    filters = []
    
    if title:
        filters.append(Book.title.ilike(f"%{title}%"))
    
    if author:
        filters.append(Author.name.ilike(f"%{author}%"))
    
    if year_from:
        filters.append(Book.year >= year_from)
    
    if year_to:
        filters.append(Book.year <= year_to)
    
    if library_id:
        filters.append(Copy.library_id == library_id)
    
    if filters:
        stmt = stmt.filter(and_(*filters))
    
    # Group and order
    stmt = stmt.group_by(Book.id, Book.title, Author.name, Book.year)
    stmt = stmt.order_by(Book.title)
    
    result = await db.execute(stmt)
    rows = result.all()
    
    # Filter by availability if requested
    results = []
    for row in rows:
        if available_only and (row.available_count or 0) == 0:
            continue
        
        results.append(
            SearchResult(
                id=row.id,
                title=row.title,
                author_name=row.author_name,
                year=row.year,
                available_count=row.available_count or 0,
                total_count=row.total_count or 0
            )
        )
    
    return SearchResponse(
        query=f"title={title}, author={author}",
        total=len(results),
        results=results
    )
