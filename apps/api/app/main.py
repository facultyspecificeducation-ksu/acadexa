"""
================================================================================
Acadexa FastAPI Application
================================================================================

Main application entry point.
Configures middleware, CORS, exception handlers, and includes routers.

Author: Acadexa Team
Version: 1.1.0
================================================================================
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.router import router
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.middleware import setup_middleware  # ← ADDED: import middleware setup

# Setup logging
setup_logging()
logger = logging.getLogger("acadexa")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting Acadexa API...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Supabase URL: {settings.SUPABASE_URL}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Acadexa API...")


# Create FastAPI app
app = FastAPI(
    title="Acadexa API",
    description="Intelligent Academic Advising System API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
)

# =============================================================================
# Middleware Setup
# =============================================================================

# Setup custom middleware (Request ID, Error Handling, Request Logging)
# This must be added BEFORE CORS to ensure request IDs are available for logging
setup_middleware(app)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,  # ← FIXED: use parsed list
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware in production
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.allowed_hosts_list,  # ← FIXED: use parsed list
    )

# Include API router
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint - API information."""
    return {
        "name": "Acadexa API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs" if settings.ENVIRONMENT != "production" else None,
    }


@app.get("/health")
async def health():
    """Simple health check for Render."""
    return {"status": "healthy"}