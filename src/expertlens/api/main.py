"""FastAPI application for ExpertLens.

This module provides the REST API layer over the core orchestrator.
FastAPI is a thin wrapper - all business logic lives in expertlens.core.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import health, sessions

app = FastAPI(
    title="ExpertLens API",
    description="Evidence-based Expert Discovery API",
    version="0.1.0",
)

# CORS configuration for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (Codespaces, localhost, etc.)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(sessions.router)


@app.get("/")
async def root() -> dict:
    """Root endpoint with API info."""
    return {
        "name": "ExpertLens API",
        "version": "0.1.0",
        "docs": "/docs",
    }
