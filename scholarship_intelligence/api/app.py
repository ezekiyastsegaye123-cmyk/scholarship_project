"""FastAPI main application for Scholarship Intelligence Student MVP."""
import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from scholarship_intelligence.api.routes import counselor, opportunities, student_profile

app = FastAPI(
    title="Scholarship Intelligence & Counselor API",
    description="Deterministic scholarship discovery, eligibility evaluation, and qualitative counselor MVP",
    version="0.2.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Suitable for local development and paired Vite frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers under /api
api_prefix = "/api"
app.include_router(opportunities.router, prefix=api_prefix)
app.include_router(student_profile.router, prefix=api_prefix)
app.include_router(counselor.router, prefix=api_prefix)


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
