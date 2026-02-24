from pydantic import BaseModel
from typing import Optional


# Token schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: Optional[int] = None  # user_id
    exp: Optional[int] = None  # expiration timestamp
    type: Optional[str] = None  # "access" or "refresh"


# Staff user schemas
class StaffUserBase(BaseModel):
    username: str
    full_name: Optional[str] = None
    is_active: bool = True
    is_admin: bool = False


class StaffUserCreate(StaffUserBase):
    password: str
    library_id: Optional[int] = None


class StaffUserUpdate(BaseModel):
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    library_id: Optional[int] = None


class StaffUserInDB(StaffUserBase):
    id: int
    library_id: Optional[int] = None

    class Config:
        from_attributes = True


class StaffUserResponse(StaffUserInDB):
    pass


# Login schema
class LoginRequest(BaseModel):
    username: str
    password: str
