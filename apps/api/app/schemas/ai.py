"""
================================================================================
AI Assistant Pydantic Schemas
================================================================================

Request/response validation schemas for AI assistant endpoints.

Author: Acadexa Team
Version: 1.0.0
================================================================================
"""

from typing import List, Dict, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Chat message in conversation."""
    
    role: str = Field(..., description="Role: user or assistant")
    content: str = Field(..., min_length=1, description="Message content")


class ChatContext(BaseModel):
    """Context for chat request."""
    
    student_id: Optional[UUID] = None


class ChatRequest(BaseModel):
    """Request schema for chat endpoint."""
    
    messages: List[ChatMessage] = Field(..., min_length=1, description="Conversation history")
    context: Optional[ChatContext] = None


class ChatResponse(BaseModel):
    """Response schema for chat endpoint."""
    
    role: str = "assistant"
    content: str
    context_used: Optional[Dict[str, Any]] = None


class ExplainRecommendationResponse(BaseModel):
    """Response schema for explain recommendation endpoint."""
    
    original_title: str
    original_description: str
    original_recommendation: Optional[str] = None
    plain_explanation: str
    issue_id: str