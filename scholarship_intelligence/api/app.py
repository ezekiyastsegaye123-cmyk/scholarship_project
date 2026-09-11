"""FastAPI main application for Scholarship Intelligence Student MVP."""
import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from scholarship_intelligence.api.routes import (
    ai_counselor,
    applications,
    auth,
    comparison,
    counselor,
    ingestion,
    opportunities,
    saved_opportunities,
    student_profile,
)

app = FastAPI(
    title="Scholarship Intelligence & Counselor API",
    description="Deterministic scholarship discovery, eligibility evaluation, and student persistence platform",
    version="0.3.0",
)

# CORS configuration: strict origin list to prevent credential leakage
allowed_origins_env = os.getenv("ALLOWED_ORIGINS")
allowed_origins = (
    [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
    if allowed_origins_env
    else [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers under /api
api_prefix = "/api"
app.include_router(auth.router, prefix=api_prefix)
app.include_router(opportunities.router, prefix=api_prefix)
app.include_router(student_profile.router, prefix=api_prefix)
app.include_router(saved_opportunities.router, prefix=api_prefix)
app.include_router(applications.router, prefix=api_prefix)
app.include_router(comparison.router, prefix=api_prefix)
app.include_router(counselor.router, prefix=api_prefix)
app.include_router(ai_counselor.router, prefix=api_prefix)
app.include_router(ingestion.router, prefix=api_prefix)


@app.get("/health")
def health_check():
    """Application liveness check."""
    return {
        "status": "healthy",
        "phase": "Phase 2 - Student MVP",
        "service": "scholarship-intelligence-api",
    }


# Static file serving for production frontend build (if built)
dist_dir = Path("frontend/dist")
if dist_dir.exists() and dist_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="static-frontend")
