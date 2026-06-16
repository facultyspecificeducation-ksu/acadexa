"""
================================================================================
Health Check Endpoint
================================================================================

Provides health check for Render deployment and Electron sidecar verification.

Author: Acadexa Team
Version: 1.0.0
================================================================================
"""

from datetime import datetime, timezone
from typing import Dict

from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check() -> Dict:
    """
    Health check endpoint.
    
    Returns:
        Status OK with timestamp and version
    """
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "service": "acadexa-api"
    }