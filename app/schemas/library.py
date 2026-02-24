from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class LibraryBase(BaseModel):
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    work_hours: Optional[str] = None


class LibraryCreate(LibraryBase):
    pass


class LibraryUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    work_hours: Optional[str] = None


class LibraryResponse(LibraryBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
