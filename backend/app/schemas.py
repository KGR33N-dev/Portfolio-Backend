from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# Blog Post Schemas
class BlogPostBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    excerpt: Optional[str] = None
    author: str = "KGR33N"
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    language: str = Field(default="pl", pattern="^(pl|en)$")
    category: str = "general"

class BlogPostCreate(BlogPostBase):
    slug: str = Field(..., min_length=1, max_length=200)
    tags: Optional[List[str]] = []

class BlogPostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    excerpt: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    category: Optional[str] = None
    is_published: Optional[bool] = None
    tags: Optional[List[str]] = None

class BlogPostPublic(BlogPostBase):
    id: int
    slug: str
    created_at: datetime
    updated_at: datetime
    is_published: bool
    published_at: Optional[datetime]
    tags: List[str] = []
    
    class Config:
        from_attributes = True

class BlogPostAdmin(BlogPostPublic):
    """Extended schema for admin operations"""
    pass

# Tag Schemas
class TagCreate(BaseModel):
    tag_name: str = Field(..., min_length=1, max_length=50)

class Tag(TagCreate):
    id: int
    post_id: int
    
    class Config:
        from_attributes = True

# User Schemas (for authentication)
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    full_name: Optional[str] = None
    bio: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None

class UserLogin(BaseModel):
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    password: str = Field(..., min_length=6)

class EmailVerificationRequest(BaseModel):
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')

class EmailVerificationConfirm(BaseModel):
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    verification_code: str = Field(..., min_length=6, max_length=6, pattern=r'^\d{6}$')

class PasswordResetRequest(BaseModel):
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')

class PasswordResetConfirm(BaseModel):
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    reset_token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)

class UserRegistrationRequest(BaseModel):
    """Initial registration request - creates unverified user"""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None
    bio: Optional[str] = None

class User(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    email_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    user: User
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"

class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str
    expires_in: int
    user: User

class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    permissions: List[str] = ["read"]
    expires_days: int = Field(default=30, ge=1, le=365)

class APIKey(BaseModel):
    id: int
    name: str
    key_preview: str  # Only first 8 chars for security
    permissions: List[str]
    created_at: datetime
    expires_at: Optional[datetime]
    is_active: bool
    
    class Config:
        from_attributes = True

class APIKeyResponse(BaseModel):
    api_key: APIKey
    full_key: str  # Only returned on creation

# Vote Schemas (for polls/voting system)
class VoteCreate(BaseModel):
    poll_name: str = Field(..., min_length=1, max_length=100)
    option: str = Field(..., min_length=1, max_length=200)

class Vote(VoteCreate):
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# API Response Schemas
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None

class PaginatedResponse(BaseModel):
    items: List[dict]
    total: int
    page: int
    pages: int
    per_page: int
