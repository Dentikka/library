from pydantic import BaseModel
from typing import List, Optional


class SearchResult(BaseModel):
    id: int
    title: str
    author_name: str
    year: Optional[int] = None
    available_count: int
    total_count: int


class SearchResponse(BaseModel):
    query: str
    total: int
    page: int
    per_page: int
    pages: int
    results: List[SearchResult]


class SearchSuggestions(BaseModel):
    query: str
    suggestions: List[str]
