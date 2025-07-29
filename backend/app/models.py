from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class BlogPost(Base):
    __tablename__ = "blog_posts"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    slug = Column(String(200), unique=True, nullable=False, index=True)
    content = Column(Text, nullable=False)
    excerpt = Column(Text)
    author = Column(String(100), default="KGR33N")
    author_id = Column(Integer, ForeignKey("users.id"))  # For authenticated authors
    
    # SEO and metadata
    meta_title = Column(String(200))
    meta_description = Column(String(300))
    
    # Language support
    language = Column(String(2), default="pl")  # 'pl' or 'en'
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Publishing
    is_published = Column(Boolean, default=False)
    published_at = Column(DateTime)
    
    # Gaming/project related
    category = Column(String(50), default="general")  # general, gamedev, python, tutorial, etc.
    tags = relationship("BlogTag", back_populates="post")
    author_user = relationship("User", back_populates="blog_posts")

class BlogTag(Base):
    __tablename__ = "blog_tags"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("blog_posts.id"))
    tag_name = Column(String(50), nullable=False)
    
    post = relationship("BlogPost", back_populates="tags")

# Enhanced User model with security features
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    
    # Profile info
    full_name = Column(String(100))
    bio = Column(Text)
    
    # Permissions
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    
    # Email verification
    email_verified = Column(Boolean, default=False)
    verification_code_hash = Column(String(255))  # Hashed verification code
    verification_token = Column(String(500))  # JWT token for verification
    verification_expires_at = Column(DateTime)
    
    # Security features
    failed_login_attempts = Column(Integer, default=0)
    account_locked_until = Column(DateTime)
    last_login = Column(DateTime)
    password_reset_token = Column(String(500))
    password_reset_expires_at = Column(DateTime)
    
    # Two-factor authentication (future feature)
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String(255))
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    blog_posts = relationship("BlogPost", back_populates="author_user")
    api_keys = relationship("APIKey", back_populates="user")

class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    key_hash = Column(String(255), unique=True, index=True, nullable=False)
    key_preview = Column(String(20), nullable=False)  # First 8 chars for display
    permissions = Column(JSON, default=["read"])  # List of permissions
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime)
    last_used = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")

class Vote(Base):
    """Model dla systemu głosowań/ankiet"""
    __tablename__ = "votes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    poll_name = Column(String(100), nullable=False)  # nazwa ankiety/głosowania
    option = Column(String(200), nullable=False)     # wybrana opcja
    created_at = Column(DateTime, server_default=func.now())
    ip_address = Column(String(45))  # For anonymous voting tracking
    
    # Relationships
    user = relationship("User")
