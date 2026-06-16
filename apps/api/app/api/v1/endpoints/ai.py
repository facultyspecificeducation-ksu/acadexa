"""
================================================================================
AI Assistant API Endpoints
================================================================================

Endpoints for AI assistant:
- Chat with context (student data + recommendations)
- Explain recommendations in plain Arabic

Rate limiting applied to these endpoints.

Author: Acadexa Team
Version: 1.0.0
================================================================================
"""

import logging
from typing import List, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Request

from app.core.dependencies import get_ai_service, require_staff
from app.core.rate_limiter import get_rate_limit_key_for_user, rate_limit
from app.services.ai_service import AIService
from app.schemas.ai import ChatRequest, ChatResponse, ExplainRecommendationResponse

logger = logging.getLogger("acadexa.api.ai")

router = APIRouter(prefix="/ai", tags=["AI Assistant"])


@router.post("/chat", response_model=ChatResponse)
@rate_limit(limit=30, window_seconds=60, key_func=get_rate_limit_key_for_user)
async def chat(
    request: Request,
    chat_request: ChatRequest,
    service: AIService = Depends(get_ai_service),
    _=Depends(require_staff),
):
    """
    Send a chat message to the AI assistant.
    
    Rate limited to 30 requests per minute per user.
    Accessible by all staff members.
    
    Context includes student data when student_id is provided.
    """
    response = await service.chat(
        messages=chat_request.messages,
        context=chat_request.context,
    )
    
    return ChatResponse(
        role=response["role"],
        content=response["content"],
        context_used=response.get("context_used"),
    )


@router.post("/explain-recommendation", response_model=ExplainRecommendationResponse)
@rate_limit(limit=10, window_seconds=60, key_func=get_rate_limit_key_for_user)
async def explain_recommendation(
    issue_id: UUID,
    service: AIService = Depends(get_ai_service),
    _=Depends(require_staff),
):
    """
    Get plain Arabic explanation for a recommendation.
    
    Rate limited to 10 requests per minute per user.
    Accessible by all staff members.
    """
    explanation = await service.explain_recommendation(issue_id)
    
    return ExplainRecommendationResponse(
        original_title=explanation["original_title"],
        original_description=explanation["original_description"],
        original_recommendation=explanation.get("original_recommendation"),
        plain_explanation=explanation["plain_explanation"],
        issue_id=explanation["issue_id"],
    )