from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import os
from .database import engine, Base
from .routers import blog, auth
from .security import limiter
import uvicorn

# Create all tables
Base.metadata.create_all(bind=engine)

# Get environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

app = FastAPI(
    title="Portfolio API",
    description="Backend API dla portfolio KGR33N",
    version="1.0.0",
    docs_url="/api/docs" if DEBUG else None,  # Disable docs in production
    redoc_url="/api/redoc" if DEBUG else None,
    openapi_url="/api/openapi.json" if DEBUG else None
)

# CORS Configuration - Production ready
# Get allowed origins from environment or use defaults
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:4321")
PRODUCTION_FRONTEND = os.getenv("PRODUCTION_FRONTEND", "https://kgr33n.com")

origins = [
    "http://localhost:4321",
    "http://localhost:4322", 
    "http://localhost:3000",
    "http://localhost:8000",
    "https://localhost:4321",
    "https://localhost:4322",
    "https://localhost:8000",
    "https://kgr33n.com",
    "https://www.kgr33n.com",
    "http://kgr33n.com",
    "http://www.kgr33n.com",
    "https://api.kgr33n.com"
]

# Add production frontend URL if provided
if PRODUCTION_FRONTEND and PRODUCTION_FRONTEND not in origins:
    origins.extend([
        PRODUCTION_FRONTEND,
        f"https://{PRODUCTION_FRONTEND.replace('https://', '').replace('http://', '')}",
        f"https://www.{PRODUCTION_FRONTEND.replace('https://', '').replace('http://', '').replace('www.', '')}"
    ])

print(f"🔧 CORS Origins: {origins}")  # Debug

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Add rate limiting middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Include routers with authentication
app.include_router(blog.router, prefix="/api/blog", tags=["blog"])
app.include_router(auth.router, prefix="/api", tags=["auth"])

@app.get("/")
async def root():
    return {"message": "Portfolio API działa! 🚀", "environment": ENVIRONMENT}

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy", 
        "message": "API is running",
        "environment": ENVIRONMENT,
        "debug": DEBUG
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True if ENVIRONMENT == 'development' else False
    )
