from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
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

class BlogTag(Base):
    __tablename__ = "blog_tags"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("blog_posts.id"))
    tag_name = Column(String(50), nullable=False)
    
    post = relationship("BlogPost", back_populates="tags")

# Future models for expanded functionality
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
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class Vote(Base):
    """Model dla systemu głosowań/ankiet"""
    __tablename__ = "votes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    poll_name = Column(String(100), nullable=False)  # nazwa ankiety/głosowania
    option = Column(String(200), nullable=False)     # wybrana opcja
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    user = relationship("User")
