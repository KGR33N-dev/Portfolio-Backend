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
