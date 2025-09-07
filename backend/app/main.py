from fastapi import FastAPI, Request, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import os
import asyncio
from datetime import datetime
from .database import init_default_languages, init_roles_and_ranks
from .routers import auth, languages, comments, roles, profile
from .routers import blog_multilingual as blog
from .security import limiter, get_current_admin_user, conditional_limit
from .schemas import ContactForm, ContactResponse
from .email_service import EmailService
from .tasks import run_maintenance_tasks
import uvicorn
import resend


resend.api_key = os.environ["RESEND_API_KEY"]

# Usunięto automatyczne tworzenie tabel - używamy Alembic migrations
# Base.metadata.create_all(bind=engine)

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

# Background task scheduler
async def periodic_cleanup():
    """Run cleanup tasks every hour"""
    while True:
        try:
            await run_maintenance_tasks()
        except Exception as e:
            print(f"Error in periodic cleanup: {e}")
        # Wait 1 hour before next cleanup
        await asyncio.sleep(3600)

# Start background tasks
@app.on_event("startup")
async def startup_event():
    """Start background tasks when application starts"""
    # Inicjalizacja danych została przeniesiona do skryptu create_admin.py
    # Uruchom: docker compose exec web python app/create_admin.py
    
    if ENVIRONMENT == "production":
        # Only run cleanup tasks in production
        asyncio.create_task(periodic_cleanup())
    print(f"🚀 Portfolio API started in {ENVIRONMENT} mode")
    print("💡 Aby zainicjalizować dane i utworzyć administratora:")
    print("   docker compose exec web python app/create_admin.py")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup when application shuts down"""
    print("👋 Portfolio API shutting down...")

# CORS Configuration - Production ready
# Get allowed origins from environment or use defaults
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:4321")
PRODUCTION_FRONTEND = os.getenv("PRODUCTION_FRONTEND", "https://kgr33n.com")

# Base origins - always allowed
origins = [
    "http://localhost:4321",     # Astro dev server
    "http://localhost:4322", 
    "http://localhost:3000",     # React/Next.js
    "http://localhost:8000",     # FastAPI
    "http://localhost:8080",     # Alternative ports
    "http://127.0.0.1:4321",     # Alternative localhost format
    "http://127.0.0.1:4322",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:8080",
    "https://localhost:4321",    # HTTPS variants
    "https://localhost:4322",
    "https://localhost:8000",
    "https://127.0.0.1:4321",
    "https://127.0.0.1:4322",
    "https://127.0.0.1:8000",
    "https://kgr33n.com",
    "https://www.kgr33n.com",
    "http://kgr33n.com",
    "http://www.kgr33n.com",
    "https://api.kgr33n.com",
    "http://api.kgr33n.com"
]

# Add FRONTEND_URL if not already in origins
if FRONTEND_URL and FRONTEND_URL not in origins:
    origins.append(FRONTEND_URL)
    print(f"✅ Added FRONTEND_URL to origins: {FRONTEND_URL}")

# Add production frontend URL if provided
if PRODUCTION_FRONTEND and PRODUCTION_FRONTEND not in origins:
    origins.extend([
        PRODUCTION_FRONTEND,
        f"https://{PRODUCTION_FRONTEND.replace('https://', '').replace('http://', '')}",
        f"https://www.{PRODUCTION_FRONTEND.replace('https://', '').replace('http://', '').replace('www.', '')}"
    ])

# Add additional origins from environment variable
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "")
if ALLOWED_ORIGINS:
    additional_origins = [origin.strip() for origin in ALLOWED_ORIGINS.split(",") if origin.strip()]
    for origin in additional_origins:
        if origin not in origins:
            origins.append(origin)
            print(f"✅ Added additional origin: {origin}")

print(f"🔧 CORS Origins: {origins}")  # Debug
print(f"🌍 Environment: {ENVIRONMENT}")
print(f"🔧 Production Frontend: {PRODUCTION_FRONTEND}")
print(f"🔧 Backend URL: {os.getenv('BACKEND_URL', 'Not set')}")

# Add CORS debugging middleware in development
if ENVIRONMENT == "development":
    @app.middleware("http")
    async def cors_debug_middleware(request: Request, call_next):
        origin = request.headers.get("origin")
        print(f"🌐 Request Origin: {origin}")
        print(f"🌐 Request Method: {request.method}")
        print(f"🌐 Request URL: {request.url}")
        
        response = await call_next(request)
        
        if origin:
            print(f"✅ CORS Origin {'allowed' if origin in origins else 'not allowed'}: {origin}")
        
        return response

# Enhanced CORS middleware for production cross-domain support
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,  # CRITICAL for cookies across domains
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Add rate limiting middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Include routers with authentication
app.include_router(blog.router, prefix="/api/blog", tags=["blog"])
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(languages.router, prefix="/api/languages", tags=["languages"])
app.include_router(comments.router, prefix="/api/comments", tags=["comments"])
app.include_router(roles.router, tags=["roles"])
app.include_router(profile.router, prefix="/api", tags=["profile"])

@app.get("/")
async def root():
    return {"message": "Portfolio API działa! 🚀", "environment": ENVIRONMENT}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat(),
        "backend_url": os.getenv("BACKEND_URL", "Not configured"),
        "production_frontend": PRODUCTION_FRONTEND
    }

@app.get("/cors-test")
async def cors_test(request: Request):
    """Test CORS configuration and cookies"""
    origin = request.headers.get("origin")
    return {
        "message": "CORS test successful",
        "origin": origin,
        "origin_allowed": origin in origins if origin else None,
        "environment": ENVIRONMENT,
        "cors_origins": origins[:5],  # Show first 5 for debugging
        "cookies_received": dict(request.cookies),
        "timestamp": datetime.utcnow().isoformat()
    }@app.post("/api/contact", response_model=ContactResponse)
@conditional_limit("3/minute")  # Rate limit: 3 requests per minute (disabled in dev)
async def send_contact_message(
    request: Request,
    contact_form: ContactForm
):
    """
    Send contact form message via email
    """
    try:
        email_service = EmailService()
        
        # Send contact form email with user's language preference
        user_language = email_service.get_user_language_from_request(request)
        success = await email_service.send_contact_form_email(
            name=contact_form.name,
            email=contact_form.email,
            subject=contact_form.subject,
            message=contact_form.message,
            language=user_language
        )
        
        if success:
            return ContactResponse(
                success=True,
                message="Wiadomość została wysłana pomyślnie! Odpowiem tak szybko jak to możliwe."
            )
        else:
            # Email service failed but we logged the message
            return ContactResponse(
                success=True,  # Still return success since message was logged
                message="Wiadomość została odebrana. W przypadku problemów z dostawą, skontaktuj się bezpośrednio."
            )
            
    except Exception as e:
        # Log error but don't expose internal details
        print(f"Contact form error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"translation_code": "CONTACT_FORM_ERROR", "message": "Wystąpił błąd podczas wysyłania wiadomości. Spróbuj ponownie później."}
        )

@app.post("/api/admin/cleanup", response_model=ContactResponse)
async def manual_cleanup(
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_admin_user)
):
    """
    Manually trigger cleanup tasks (admin only)
    """
    try:
        # Run cleanup in background
        background_tasks.add_task(run_maintenance_tasks)
        
        return ContactResponse(
            success=True,
            message="Zadania czyszczenia zostały uruchomione w tle."
        )
    except Exception as e:
        print(f"Manual cleanup error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"translation_code": "CLEANUP_TASK_ERROR", "message": "Wystąpił błąd podczas uruchamiania zadań czyszczenia."}
        )


if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True if ENVIRONMENT == 'development' else False
    )
