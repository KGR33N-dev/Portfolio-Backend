from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# Blog Post Translation Schemas
class BlogPostTranslationBase(BaseModel):
    language_code: str = Field(..., min_length=2, max_length=10)
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    excerpt: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None

class BlogPostTranslationCreate(BlogPostTranslationBase):
    pass

class BlogPostTranslationUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    excerpt: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None

class BlogPostTranslationPublic(BlogPostTranslationBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Blog Post Schemas (Main post without language-specific content)
class BlogPostBase(BaseModel):
    slug: str = Field(..., min_length=1, max_length=200)
    author: str = "KGR33N"
    category: str = "general"
    featured_image: Optional[str] = None

class BlogPostCreate(BlogPostBase):
    tags: Optional[List[str]] = []
    translations: List[BlogPostTranslationCreate] = Field(..., min_items=1)

class BlogPostUpdate(BaseModel):
    category: Optional[str] = None
    is_published: Optional[bool] = None
    featured_image: Optional[str] = None
    tags: Optional[List[str]] = None
    translations: Optional[List[BlogPostTranslationCreate]] = None

class BlogPostPublic(BlogPostBase):
    id: int
    created_at: datetime
    updated_at: datetime
    is_published: bool
    published_at: Optional[datetime]
    tags: List[str] = []
    translations: List[BlogPostTranslationPublic] = []
    
    class Config:
        from_attributes = True

class BlogPostAdmin(BlogPostPublic):
    """Extended schema for admin operations"""
    author_id: Optional[int] = None

# Single language view for easier frontend consumption
class BlogPostSingleLanguage(BaseModel):
    id: int
    slug: str
    title: str
    content: str
    excerpt: Optional[str] = None
    author: str
    author_id: Optional[int] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    language_code: str
    category: str
    featured_image: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_published: bool
    published_at: Optional[datetime]
    tags: List[str] = []
    
    class Config:
        from_attributes = True

# Language Schemas
class LanguageCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=10, pattern="^[a-z-]+$")
    name: str = Field(..., min_length=1, max_length=100)
    native_name: str = Field(..., min_length=1, max_length=100)

class LanguageUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    native_name: Optional[str] = Field(None, min_length=1, max_length=100)
    is_active: Optional[bool] = None

class Language(BaseModel):
    id: int
    code: str
    name: str
    native_name: str
    is_active: bool
    created_at: datetime
    created_by: Optional[int] = None
    
    class Config:
        from_attributes = True

# Contact Schemas
class ContactForm(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    subject: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=10, max_length=2000)

class ContactResponse(BaseModel):
    success: bool
    message: str

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
    language: Optional[str] = Field(default="pl", description="Preferred language for email (pl/en)")

class EmailVerificationConfirm(BaseModel):
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    verification_code: str = Field(..., min_length=6, max_length=6, pattern=r'^\d{6}$')

class PasswordResetRequest(BaseModel):
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    language: Optional[str] = Field(default="pl", description="Preferred language for email (pl/en)")

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
    language: Optional[str] = Field(default="pl", description="Preferred language for email (pl/en)")

class User(UserBase):
    id: int
    is_active: bool
    email_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    user: User
    message: Optional[str] = "Login successful"

class AuthResponse(BaseModel):
    success: bool = True
    message: str = "Authentication successful" 
    user: User

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

# Comment Schemas
class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)
    parent_id: Optional[int] = None

class CommentUpdate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)

# Author info with role and rank for comments
class CommentAuthor(BaseModel):
    id: Optional[int] = None
    username: str
    role: Optional["UserRole"] = None
    rank: Optional["UserRank"] = None
    
    class Config:
        from_attributes = True

class CommentLikeCreate(BaseModel):
    is_like: bool  # true = like, false = dislike

class Comment(BaseModel):
    id: int
    post_id: int
    user_id: int
    parent_id: Optional[int] = None
    content: str
    is_deleted: bool
    author: "CommentAuthor"  # Enhanced author info with role and rank
    created_at: datetime
    updated_at: datetime
    
    # Computed fields
    likes_count: Optional[int] = 0
    dislikes_count: Optional[int] = 0
    user_like_status: Optional[bool] = None  # null = no like, true = liked, false = disliked
    replies_count: Optional[int] = 0
    
    class Config:
        from_attributes = True

class CommentWithReplies(Comment):
    replies: List['CommentWithReplies'] = []

class CommentLike(BaseModel):
    id: int
    comment_id: int
    user_id: int
    is_like: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# API Response Schemas
class APIResponse(BaseModel):
    success: bool
    message: str
    type: Optional[str] = None
    translation_code: Optional[str] = None
    data: Optional[dict] = None

class PaginatedResponse(BaseModel):
    items: List[dict]
    total: int
    page: int
    pages: int
    per_page: int

# 🎯 USER ROLES AND RANKS SCHEMAS
class UserRoleBase(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None
    color: str = "#6c757d"
    permissions: List[str] = []
    level: int = 0

class UserRole(UserRoleBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserRankBase(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None
    icon: str = "👤"
    color: str = "#28a745"
    requirements: dict = {}
    level: int = 0

class UserRank(UserRankBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserWithRoleRank(BaseModel):
    """Extended user model with role and rank information"""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    bio: Optional[str] = None
    is_active: bool
    email_verified: bool
    created_at: datetime
    
    # Role and rank info
    role: Optional[UserRole] = None
    rank: Optional[UserRank] = None
    
    # Statistics
    total_comments: int = 0
    total_likes_received: int = 0
    total_posts: int = 0
    reputation_score: int = 0
    
    # Helper fields (computed)
    display_role: Optional[str] = None
    display_rank: Optional[str] = None
    role_color: Optional[str] = None
    rank_icon: Optional[str] = None
    
    class Config:
        from_attributes = True
