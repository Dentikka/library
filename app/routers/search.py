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
    
    # Search in title or author name (case-insensitive for both ASCII and Cyrillic)
    # Using multiple patterns for case variations due to SQLite unicode limitations
    search_patterns = [
        f"%{query}%",          # original case
        f"%{query.lower()}%",  # lowercase
        f"%{query.upper()}%",  # uppercase
        f"%{query.capitalize()}%",  # capitalized
    ]
    
    # Build OR conditions for all case variations
    title_conditions = [Book.title.like(p) for p in search_patterns]
    author_conditions = [Author.name.like(p) for p in search_patterns]
    
    stmt = stmt.filter(
        or_(
            or_(*title_conditions),
            or_(*author_conditions)
        )
    )
    
    # Group by book and author
    stmt = stmt.group_by(Book.id, Book.title, Author.name, Book.year)
    
    # Order by title
    stmt = stmt.order_by(Book.title)
    
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
    
    # Get matching book titles (case-insensitive for Cyrillic)
    search_patterns = [f"%{query}%", f"%{query.lower()}%", f"%{query.upper()}%", f"%{query.capitalize()}%"]
    book_conditions = [Book.title.like(p) for p in search_patterns]
    author_conditions = [Author.name.like(p) for p in search_patterns]
    
    book_stmt = (
        select(Book.title)
        .filter(or_(*book_conditions))
        .limit(limit)
    )
    
    # Get matching author names
    author_stmt = (
        select(Author.name)
        .filter(or_(*author_conditions))
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
        title_patterns = [f"%{title}%", f"%{title.lower()}%", f"%{title.upper()}%", f"%{title.capitalize()}%"]
        filters.append(or_(*[Book.title.like(p) for p in title_patterns]))
    
    if author:
        author_patterns = [f"%{author}%", f"%{author.lower()}%", f"%{author.upper()}%", f"%{author.capitalize()}%"]
        filters.append(or_(*[Author.name.like(p) for p in author_patterns]))
    
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
