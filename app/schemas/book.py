from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class BookBase(BaseModel):
    title: str
    isbn: Optional[str] = None
    year: Optional[int] = None
    description: Optional[str] = None


class BookCreate(BookBase):
    author_id: int


class BookUpdate(BaseModel):
    title: Optional[str] = None
    author_id: Optional[int] = None
    isbn: Optional[str] = None
    year: Optional[int] = None
    description: Optional[str] = None


class BookInDB(BookBase):
    id: int
    author_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BookResponse(BookInDB):
    author_name: Optional[str] = None
    available_count: int = 0
    total_count: int = 0
    cover_url: Optional[str] = None


class BookDetailResponse(BookResponse):
    copies_by_library: List[dict] = []


class CopyBase(BaseModel):
    book_id: int
    library_id: int
    inventory_number: str
    status: str = "available"


class CopyCreate(CopyBase):
    pass


class CopyUpdate(BaseModel):
    library_id: Optional[int] = None
    inventory_number: Optional[str] = None
    status: Optional[str] = None


class CopyInDB(CopyBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class CopyResponse(CopyInDB):
    library_name: Optional[str] = None
    book_title: Optional[str] = None
