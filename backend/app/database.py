from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable must be set")

print(f"🔗 Connecting to database: {DATABASE_URL.split('@')[0]}@****")  # Hide password in logs

# Create SQLAlchemy engine
# PostgreSQL configuration with production settings
engine = create_engine(
    DATABASE_URL, 
    echo=False,  # Disable SQL logging in production
    pool_size=20,  # Increase pool size for production
    max_overflow=30,
    pool_timeout=30,
    pool_recycle=3600,  # Recycle connections every hour
    pool_pre_ping=True  # Validate connections before use
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_default_languages():
    """Initialize default languages in the system"""
    from app.models import Language
    
    db = SessionLocal()
    try:
        # Check if languages already exist
        existing_count = db.query(Language).count()
        if existing_count > 0:
            return  # Languages already exist
        
        # Add default languages
        default_languages = [
            {
                "code": "en",
                "name": "English",
                "native_name": "English",
                "is_active": True
            },
            {
                "code": "pl", 
                "name": "Polish",
                "native_name": "Polski",
                "is_active": True
            }
        ]
        
        for lang_data in default_languages:
            language = Language(**lang_data)
            db.add(language)
        
        db.commit()
        print("✅ Initialized default languages: English, Polish")
        
    except Exception as e:
        print(f"❌ Error during languages initialization: {e}")
        db.rollback()
    finally:
        db.close()

def init_roles_and_ranks():
    """Initialize default roles and ranks in the system"""
    from app.models import UserRole, UserRank, UserRoleEnum, UserRankEnum
    
    db = SessionLocal()
    try:
        # Check if roles and ranks already exist
        existing_roles = db.query(UserRole).count()
        existing_ranks = db.query(UserRank).count()
        
        if existing_roles > 0 and existing_ranks > 0:
            return  # Roles and ranks already exist
        
        # 🎯 USER ROLES
        if existing_roles == 0:
            roles_data = [
                {
                    "name": UserRoleEnum.USER,
                    "display_name": "User",
                    "description": "Regular blog user",
                    "color": "#6c757d",
                    "permissions": ["comment.create", "comment.like", "profile.edit"],
                    "level": 1,
                    "is_active": True
                },
                {
                    "name": UserRoleEnum.MODERATOR,
                    "display_name": "Moderator",
                    "description": "Blog moderator with moderation permissions",
                    "color": "#fd7e14",
                    "permissions": [
                        "comment.create", "comment.like", "comment.moderate", 
                        "post.moderate", "user.moderate", "profile.edit"
                    ],
                    "level": 50,
                    "is_active": True
                },
                {
                    "name": UserRoleEnum.ADMIN,
                    "display_name": "Administrator",
                    "description": "Blog administrator with full permissions",
                    "color": "#dc3545",
                    "permissions": [
                        "comment.create", "comment.like", "comment.moderate", "comment.delete",
                        "post.create", "post.edit", "post.delete", "post.publish",
                        "user.manage", "role.manage", "system.admin"
                    ],
                    "level": 100,
                    "is_active": True
                }
            ]
            
            for role_data in roles_data:
                role = UserRole(**role_data)
                db.add(role)
            print("✅ Initialized default roles")
        
        # 🏆 USER RANKS
        if existing_ranks == 0:
            ranks_data = [
                {
                    "name": UserRankEnum.NEWBIE,
                    "display_name": "New User",
                    "description": "Newly registered user",
                    "icon": "👶",
                    "color": "#17a2b8",
                    "requirements": {"comments": 0, "likes": 0},
                    "level": 1
                },
                {
                    "name": UserRankEnum.REGULAR,
                    "display_name": "Regular User",
                    "description": "Active community member",
                    "icon": "👤",
                    "color": "#28a745",
                    "requirements": {"comments": 5, "likes": 10},
                    "level": 2
                },
                {
                    "name": UserRankEnum.TRUSTED,
                    "display_name": "Trusted User",
                    "description": "Experienced and trusted member",
                    "icon": "🤝",
                    "color": "#007bff",
                    "requirements": {"comments": 25, "likes": 50},
                    "level": 3
                },
                {
                    "name": UserRankEnum.STAR,
                    "display_name": "Community Star",
                    "description": "Outstanding community member",
                    "icon": "⭐",
                    "color": "#ffc107",
                    "requirements": {"comments": 100, "likes": 200},
                    "level": 4
                },
                {
                    "name": UserRankEnum.LEGEND,
                    "display_name": "Legend",
                    "description": "Legendary community member",
                    "icon": "🏆",
                    "color": "#6f42c1",
                    "requirements": {"comments": 500, "likes": 1000},
                    "level": 5
                },
                {
                    "name": UserRankEnum.VIP,
                    "display_name": "VIP",
                    "description": "Highest rank - VIP community member",
                    "icon": "👑",
                    "color": "#fd7e14",
                    "requirements": {"comments": 1000, "likes": 2000},
                    "level": 6
                }
            ]
            
            for rank_data in ranks_data:
                rank = UserRank(**rank_data)
                db.add(rank)
            print("✅ Initialized default ranks")
        
        db.commit()
        
    except Exception as e:
        print(f"❌ Error during roles and ranks initialization: {e}")
        db.rollback()
    finally:
        db.close()
