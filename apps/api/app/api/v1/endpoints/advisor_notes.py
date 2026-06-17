"""
================================================================================
Advisor Notes Endpoints
================================================================================

Implements the Advisor Notes CRUD required by the API spec:
- GET /api/v1/students/:student_id/notes
- POST /api/v1/students/:student_id/notes
- PATCH /api/v1/notes/:note_id
- DELETE /api/v1/notes/:note_id

Author: Acadexa Team
Version: 1.0.0
================================================================================
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from app.core.dependencies import get_advisor_service, require_staff, get_current_user
from app.core.exceptions import NotFoundError
from app.core.security import SecurityContext
from app.schemas.student import PrerequisiteStatusResponse  # (keeps import ordering stable; no new schemas)
from app.services.advisor_service import AdvisorService

logger = logging.getLogger("acadexa.api.advisor_notes")

router = APIRouter(tags=["Advisor Notes"])


class NoteCreateRequest(BaseModel):
    note: str


class NoteUpdateRequest(BaseModel):
    note: str


@router.get("/students/{student_id}/notes", status_code=status.HTTP_200_OK)
async def list_student_notes(
    student_id: UUID,
    limit: int = 50,
    offset: int = 0,
    service: AdvisorService = Depends(get_advisor_service),
    _=Depends(require_staff),
):
    notes, total = await service.get_student_notes(student_id=student_id, limit=limit, offset=offset)
    # Spec lists all notes; keep a minimal shape.
    return notes


@router.post("/students/{student_id}/notes", status_code=status.HTTP_201_CREATED)
async def create_student_note(
    student_id: UUID,
    payload: NoteCreateRequest,
    current_user: SecurityContext = Depends(get_current_user),
    service: AdvisorService = Depends(get_advisor_service),
    _=Depends(require_staff),
):
    created = await service.create_note(
        student_id=student_id,
        advisor_id=UUID(current_user.user_id),
        note_text=payload.note,
    )
    return {
        "id": created.get("id"),
        "student_id": created.get("student_id"),
        "advisor_id": created.get("advisor_id"),
        "note": created.get("note"),
        "created_at": created.get("created_at"),
        "updated_at": created.get("updated_at"),
    }


@router.patch("/notes/{note_id}", status_code=status.HTTP_200_OK)
async def update_note(
    note_id: UUID,
    payload: NoteUpdateRequest,
    current_user: SecurityContext = Depends(get_current_user),
    service: AdvisorService = Depends(get_advisor_service),
    _=Depends(require_staff),
):
    updated = await service.update_note(
        note_id=note_id,
        note_text=payload.note,
        user_id=UUID(current_user.user_id),
        is_admin=current_user.is_admin,
    )
    return {
        "id": updated.get("id"),
        "student_id": updated.get("student_id"),
        "advisor_id": updated.get("advisor_id"),
        "note": updated.get("note"),
        "created_at": updated.get("created_at"),
        "updated_at": updated.get("updated_at"),
    }


@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: UUID,
    current_user: SecurityContext = Depends(get_current_user),
    service: AdvisorService = Depends(get_advisor_service),
    _=Depends(require_staff),
):
    await service.delete_note(
        note_id=note_id,
        user_id=UUID(current_user.user_id),
        is_admin=current_user.is_admin,
    )
    return None

