from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from decouple import config
from .database import engine, Base
from .routers import blog, auth
import uvicorn

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Portfolio API",
    description="Backend API dla portfolio KGR33N",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS Configuration
origins = config('CORS_ORIGINS', default='http://localhost:4321').split(',')

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(blog.router, prefix="/api/blog", tags=["blog"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])

@app.get("/")
async def root():
    return {"message": "Portfolio API działa! 🚀"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "API is running"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True if config('ENVIRONMENT', default='development') == 'development' else False
    )
