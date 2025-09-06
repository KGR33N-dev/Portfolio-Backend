from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, UniqueConstraint, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum
from app.database import Base

# Enums for user roles and ranks
class UserRoleEnum(str, Enum):
    """Main user roles"""
    USER = "role.user"           # Regular user
    MODERATOR = "role.moderator" # Moderator (future)
    ADMIN = "role.admin"         # Administrator

class UserRankEnum(str, Enum):
    """User ranks/badges"""
    NEWBIE = "rank.newbie"       # New user
    REGULAR = "rank.regular"     # Regular user
    TRUSTED = "rank.trusted"     # Trusted user
    STAR = "rank.star"          # Community star
    LEGEND = "rank.legend"      # Legend (future)
    VIP = "rank.vip"           # VIP (future)

class UserRole(Base):
    """Model for user roles - modular permission system"""
    __tablename__ = "user_roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(SQLEnum(UserRoleEnum), unique=True, nullable=False, index=True)
    display_name = Column(String(50), nullable=False)  # "Administrator", "Moderator"
    description = Column(Text)
    color = Column(String(7), default="#6c757d")  # Hex color for UI
    
    # Permissions - JSON with list of permissions
    permissions = Column(JSON, default=[])
    
    # Hierarchy - higher level = more permissions
    level = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    users = relationship("User", back_populates="role")

class UserRank(Base):
    """Model for user ranks/badges - gamification system"""
    __tablename__ = "user_ranks"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(SQLEnum(UserRankEnum), unique=True, nullable=False, index=True)
    display_name = Column(String(50), nullable=False)  # "Star", "Legend"
    description = Column(Text)
    icon = Column(String(10), default="👤")  # Emoji or CSS class
    color = Column(String(7), default="#28a745")  # Hex color
    
    # Requirements to get this rank
    requirements = Column(JSON, default={})  # {"comments": 100, "likes": 500}
    
    # Rank hierarchy
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
    
    # 🎯 NEW MODULAR ROLE AND RANK SYSTEM
    role_id = Column(Integer, ForeignKey("user_roles.id"), nullable=True)
    rank_id = Column(Integer, ForeignKey("user_ranks.id"), nullable=True)
    
    # Statistics for automatic rank upgrades
    total_comments = Column(Integer, default=0)
    total_likes_received = Column(Integer, default=0)
    total_posts = Column(Integer, default=0)
    reputation_score = Column(Integer, default=0)  # General reputation score
    
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
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan")
    comment_likes = relationship("CommentLike", back_populates="user", cascade="all, delete-orphan")
    
    # 🎯 UTILITY METHODS for role and rank system
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission"""
            
        if self.role and self.role.permissions:
            return permission in self.role.permissions
        return False
    
    def has_role(self, role_name: str) -> bool:
        """Check if user has specific role"""
        if self.role:
            return self.role.name == role_name
        return False
    
    def get_display_role(self) -> str:
        """Get readable role name"""
        if self.role:
            return self.role.display_name
        return "User"  # Default role name if not set
    
    def get_display_rank(self) -> str:
        """Get readable rank name"""
        if self.rank:
            return self.rank.display_name
        return "👤 New User"

    def get_role_color(self) -> str:
        """Get role color for UI"""
        if self.role:
            return self.role.color
    
    def get_rank_icon(self) -> str:
        """Get rank icon"""
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
    """Model for voting/poll system"""
    __tablename__ = "votes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    poll_name = Column(String(100), nullable=False)  # poll/vote name
    option = Column(String(200), nullable=False)     # selected option
    created_at = Column(DateTime, server_default=func.now())
    ip_address = Column(String(45))  # For anonymous voting tracking
    
    # Relationships
    user = relationship("User")

class Language(Base):
    """Model for available post languages"""
    __tablename__ = "languages"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, nullable=False, index=True)  # e.g. 'en', 'pl', 'de', 'fr'
    name = Column(String(100), nullable=False)  # e.g. 'English', 'Polish', 'German'
    native_name = Column(String(100), nullable=False)  # e.g. 'English', 'Polski', 'Deutsch'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    creator = relationship("User")

class Comment(Base):
    """Model for blog post comments"""
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("blog_posts.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    parent_id = Column(Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=True)  # For replies
    
    # Content
    content = Column(Text, nullable=False)
    
    # Moderation
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
    """Model for comment likes/dislikes"""
    __tablename__ = "comment_likes"
    
    id = Column(Integer, primary_key=True, index=True)
    comment_id = Column(Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=False, index=True)  # ⚡ Index for fast queries
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)  # ⚡ Index for fast queries
    
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
