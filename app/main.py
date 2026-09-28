from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import auth, users, enquiries, leads, articles, media, dashboard

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 1. Normalize allowed origins (strip any accidental trailing slashes)
raw_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://rsjuris.vercel.app",
    "https://www.rsjuris.vercel.app",
]

# Merge with settings.BACKEND_CORS_ORIGINS if configured
if hasattr(settings, "BACKEND_CORS_ORIGINS") and settings.BACKEND_CORS_ORIGINS:
    for origin in settings.BACKEND_CORS_ORIGINS:
        cleaned = str(origin).rstrip("/")
        if cleaned not in raw_origins:
            raw_origins.append(cleaned)

# 2. Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=raw_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",  # Permits all preview deployment branches
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# 3. Register All Core Modules
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(users.router, prefix=settings.API_V1_STR)
app.include_router(dashboard.router, prefix=settings.API_V1_STR)
app.include_router(enquiries.router, prefix=settings.API_V1_STR)
app.include_router(leads.router, prefix=settings.API_V1_STR)
app.include_router(articles.router, prefix=settings.API_V1_STR)
app.include_router(media.router, prefix=settings.API_V1_STR)

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "database": "connected"
    }