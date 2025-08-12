from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, UniqueConstraint, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum
from app.database import Base

# Enums for user roles and ranks
class UserRoleEnum(str, Enum):
    """Główne role użytkowników"""
    USER = "user"           # Zwykły użytkownik
    MODERATOR = "moderator" # Moderator (przyszłość)
    ADMIN = "admin"         # Administrator

class UserRankEnum(str, Enum):
    """Rangi/odznaczenia użytkowników"""
    NEWBIE = "newbie"       # Nowy użytkownik
    REGULAR = "regular"     # Regularny użytkownik
    TRUSTED = "trusted"     # Zaufany użytkownik
    STAR = "star"          # Gwiazda społeczności
    LEGEND = "legend"      # Legenda (przyszłość)
    VIP = "vip"           # VIP (przyszłość)

class UserRole(Base):
    """Model dla ról użytkowników - modularny system uprawnień"""
    __tablename__ = "user_roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(SQLEnum(UserRoleEnum), unique=True, nullable=False, index=True)
    display_name = Column(String(50), nullable=False)  # "Administrator", "Moderator"
    description = Column(Text)
    color = Column(String(7), default="#6c757d")  # Hex color dla UI
    
    # Uprawnienia - JSON z listą uprawnień
    permissions = Column(JSON, default=[])
    
    # Hierarchia - wyższy poziom = więcej uprawnień
    level = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    users = relationship("User", back_populates="role")

class UserRank(Base):
    """Model dla rang/odznaczeń użytkowników - system gamifikacji"""
    __tablename__ = "user_ranks"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(SQLEnum(UserRankEnum), unique=True, nullable=False, index=True)
    display_name = Column(String(50), nullable=False)  # "⭐ Gwiazda", "🏆 Legenda"
    description = Column(Text)
    icon = Column(String(10), default="👤")  # Emoji lub CSS class
    color = Column(String(7), default="#28a745")  # Hex color
    
    # Wymagania do uzyskania rangi
    requirements = Column(JSON, default={})  # {"comments": 100, "likes": 500}
    
    # Hierarchia rang
    level = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    users = relationship("User", back_populates="rank")

class BlogPost(Base):
    __tablename__ = "blog_posts"
    
    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(200), unique=True, nullable=False, index=True)  # Base slug (language-independent)
    author = Column(String(100), default="KGR33N")
    author_id = Column(Integer, ForeignKey("users.id"))  # For authenticated authors
    
    # SEO and metadata
    featured_image = Column(String(500))  # URL to featured image
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Publishing
    is_published = Column(Boolean, default=False)
    published_at = Column(DateTime)
    
    # Gaming/project related
    category = Column(String(50), default="general")  # general, gamedev, python, tutorial, etc.
    
    # Relationships
    tags = relationship("BlogTag", back_populates="post")
    author_user = relationship("User", back_populates="blog_posts")
    translations = relationship("BlogPostTranslation", back_populates="post", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")

class BlogPostTranslation(Base):
    __tablename__ = "blog_post_translations"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("blog_posts.id", ondelete="CASCADE"), nullable=False)
    language_code = Column(String(10), ForeignKey("languages.code"), nullable=False)
    
    # Content fields per language
    title = Column(String(200), nullable=False, index=True)
    content = Column(Text, nullable=False)
    excerpt = Column(Text)
    
    # SEO per language
    meta_title = Column(String(200))
    meta_description = Column(String(300))
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    post = relationship("BlogPost", back_populates="translations")
    language = relationship("Language")
    
    # Ensure one translation per language per post
    __table_args__ = (UniqueConstraint('post_id', 'language_code', name='uq_post_language'),)

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
    
    # Permissions and roles
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)  # ⚠️ Deprecated - używaj role_id
    
    # 🎯 NOWY MODULARNY SYSTEM RÓL I RANG
    role_id = Column(Integer, ForeignKey("user_roles.id"), nullable=True)
    rank_id = Column(Integer, ForeignKey("user_ranks.id"), nullable=True)
    
    # Statystyki do automatycznego upgradu rang
    total_comments = Column(Integer, default=0)
    total_likes_received = Column(Integer, default=0)
    total_posts = Column(Integer, default=0)
    reputation_score = Column(Integer, default=0)  # Ogólny score reputacji
    
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
    
    # Account expiration for unverified accounts
    account_expires_at = Column(DateTime)  # Account will be deleted if not verified by this time
    
    # Two-factor authentication (future feature)
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String(255))
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    role = relationship("UserRole", back_populates="users")
    rank = relationship("UserRank", back_populates="users")
    blog_posts = relationship("BlogPost", back_populates="author_user")
    api_keys = relationship("APIKey", back_populates="user")
    comments = relationship("Comment", back_populates="user")
    comment_likes = relationship("CommentLike", back_populates="user")
    
    # 🎯 UTILITY METHODS dla systemu ról i rang
    def has_permission(self, permission: str) -> bool:
        """Sprawdź czy użytkownik ma określone uprawnienie"""
        # Backward compatibility
        if self.is_admin:
            return True
            
        if self.role and self.role.permissions:
            return permission in self.role.permissions
        return False
    
    def has_role(self, role_name: str) -> bool:
        """Sprawdź czy użytkownik ma określoną rolę"""
        if self.role:
            return self.role.name == role_name
        # Backward compatibility
        if role_name == "admin" and self.is_admin:
            return True
        return False
    
    def get_display_role(self) -> str:
        """Pobierz czytelną nazwę roli"""
        if self.role:
            return self.role.display_name
        return "Administrator" if self.is_admin else "Użytkownik"
    
    def get_display_rank(self) -> str:
        """Pobierz czytelną nazwę rangi"""
        if self.rank:
            return self.rank.display_name
        return "👤 Nowy użytkownik"
    
    def get_role_color(self) -> str:
        """Pobierz kolor roli dla UI"""
        if self.role:
            return self.role.color
        return "#dc3545" if self.is_admin else "#6c757d"
    
    def get_rank_icon(self) -> str:
        """Pobierz ikonę rangi"""
        if self.rank:
            return self.rank.icon
        return "👤"

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

class Language(Base):
    """Model dla dostępnych języków postów"""
    __tablename__ = "languages"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, nullable=False, index=True)  # np. 'en', 'pl', 'de', 'fr'
    name = Column(String(100), nullable=False)  # np. 'English', 'Polski', 'Deutsch'
    native_name = Column(String(100), nullable=False)  # np. 'English', 'Polski', 'Deutsch'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    creator = relationship("User")

class Comment(Base):
    """Model dla komentarzy do postów bloga"""
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("blog_posts.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    parent_id = Column(Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=True)  # For replies
    
    # Content
    content = Column(Text, nullable=False)
    
    # Moderation
    is_approved = Column(Boolean, default=True)  # For moderation system
    is_deleted = Column(Boolean, default=False)  # Soft delete
    
    # Tracking
    ip_address = Column(String(45))
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    post = relationship("BlogPost", back_populates="comments")
    user = relationship("User", back_populates="comments")
    parent = relationship("Comment", remote_side=[id], back_populates="replies")
    replies = relationship("Comment", back_populates="parent", cascade="all, delete-orphan")
    likes = relationship("CommentLike", back_populates="comment", cascade="all, delete-orphan")

class CommentLike(Base):
    """Model dla polubień komentarzy"""
    __tablename__ = "comment_likes"
    
    id = Column(Integer, primary_key=True, index=True)
    comment_id = Column(Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=False, index=True)  # ⚡ Index dla szybkich zapytań
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)  # ⚡ Index dla szybkich zapytań
    
    # Like type: true = like, false = dislike
    is_like = Column(Boolean, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    comment = relationship("Comment", back_populates="likes")
    user = relationship("User", back_populates="comment_likes")
    
    # Ensure one like/dislike per user per comment
    __table_args__ = (UniqueConstraint('comment_id', 'user_id', name='uq_comment_user_like'),)
