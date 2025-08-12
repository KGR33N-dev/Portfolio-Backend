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
    """Inicjalizuje domyślne języki w systemie"""
    from app.models import Language
    
    db = SessionLocal()
    try:
        # Sprawdź czy już istnieją języki
        existing_count = db.query(Language).count()
        if existing_count > 0:
            return  # Języki już istnieją
        
        # Dodaj domyślne języki
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
        print("✅ Zainicjalizowano domyślne języki: English, Polski")
        
    except Exception as e:
        print(f"❌ Błąd podczas inicjalizacji języków: {e}")
        db.rollback()
    finally:
        db.close()

def init_roles_and_ranks():
    """Inicjalizuje domyślne role i rangi w systemie"""
    from app.models import UserRole, UserRank, UserRoleEnum, UserRankEnum
    
    db = SessionLocal()
    try:
        # Sprawdź czy już istnieją role
        existing_roles = db.query(UserRole).count()
        existing_ranks = db.query(UserRank).count()
        
        if existing_roles > 0 and existing_ranks > 0:
            return  # Role i rangi już istnieją
        
        # 🎯 ROLE UŻYTKOWNIKÓW
        if existing_roles == 0:
            roles_data = [
                {
                    "name": UserRoleEnum.USER,
                    "display_name": "Użytkownik",
                    "description": "Zwykły użytkownik bloga",
                    "color": "#6c757d",
                    "permissions": ["comment.create", "comment.like", "profile.edit"],
                    "level": 1,
                    "is_active": True
                },
                {
                    "name": UserRoleEnum.ADMIN,
                    "display_name": "Administrator",
                    "description": "Administrator bloga z pełnymi uprawnieniami",
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
            print("✅ Zainicjalizowano domyślne role")
        
        # 🏆 RANGI UŻYTKOWNIKÓW
        if existing_ranks == 0:
            ranks_data = [
                {
                    "name": UserRankEnum.NEWBIE,
                    "display_name": "👶 Nowy użytkownik",
                    "description": "Świeżo zarejestrowany użytkownik",
                    "icon": "👶",
                    "color": "#17a2b8",
                    "requirements": {"comments": 0, "likes": 0},
                    "level": 1
                },
                {
                    "name": UserRankEnum.REGULAR,
                    "display_name": "👤 Regularny użytkownik",
                    "description": "Aktywny członek społeczności",
                    "icon": "👤",
                    "color": "#28a745",
                    "requirements": {"comments": 5, "likes": 10},
                    "level": 2
                },
                {
                    "name": UserRankEnum.TRUSTED,
                    "display_name": "🤝 Zaufany użytkownik",
                    "description": "Doświadczony i zaufany członek",
                    "icon": "🤝",
                    "color": "#007bff",
                    "requirements": {"comments": 25, "likes": 50},
                    "level": 3
                },
                {
                    "name": UserRankEnum.STAR,
                    "display_name": "⭐ Gwiazda społeczności",
                    "description": "Wybitny członek społeczności",
                    "icon": "⭐",
                    "color": "#ffc107",
                    "requirements": {"comments": 100, "likes": 200},
                    "level": 4
                }
            ]
            
            for rank_data in ranks_data:
                rank = UserRank(**rank_data)
                db.add(rank)
            print("✅ Zainicjalizowano domyślne rangi")
        
        db.commit()
        
    except Exception as e:
        print(f"❌ Błąd podczas inicjalizacji ról i rang: {e}")
        db.rollback()
    finally:
        db.close()
