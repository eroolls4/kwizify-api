from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserBase(BaseModel):
    """Base model for user data."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr

class UserCreate(UserBase):
    """Model for user creation with password."""
    password: str = Field(..., min_length=8)

class UserResponse(UserBase):
    """Model for user data response."""
    id: int
    is_active: bool

class Token(BaseModel):
    """Model for authentication token response."""
    access_token: str
    token_type: str
    user: UserResponse

class TokenData(BaseModel):
    """Model for token payload data."""
    email: Optional[str] = None
    user_id: Optional[int] = None