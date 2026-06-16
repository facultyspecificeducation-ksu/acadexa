"""
================================================================================
Grade Scale Service
================================================================================

Business logic for grade scale management:
- Fetch all grade scale entries
- Update grade scale entries
- Grade point lookup for parser and inference engine

Security: Accepts authenticated Supabase client for RLS compliance.

Author: Acadexa Team
Version: 1.1.0
================================================================================
"""

import logging
import time
from typing import Dict, List, Optional

from supabase import Client

from app.core.exceptions import NotFoundError
from app.schemas.grade_scale import GradeScaleUpdate

logger = logging.getLogger("acadexa.services.grade_scale")


class GradeScaleService:
    """
    Service for grade scale management with RLS-compliant client.
    """
    
    def __init__(self, supabase_client: Client):
        """
        Initialize GradeScaleService with authenticated Supabase client.
        
        Args:
            supabase_client: Supabase client with user's JWT token.
                           Used for RLS-compliant read/write operations.
        """
        self._supabase = supabase_client
        self._cache = None
        self._cache_timestamp = None
    
    async def get_all(self) -> List[Dict]:
        """
        Get all grade scale entries.
        
        Returns:
            List of grade scale dictionaries
        """
        result = self._supabase.table("grade_scale")\
            .select("*")\
            .order("points", desc=True)\
            .execute()
        
        return result.data or []
    
    async def get_by_letter(self, grade_letter: str) -> Optional[Dict]:
        """
        Get grade scale entry by letter.
        
        Args:
            grade_letter: Grade letter (e.g., 'A', 'B+', 'W')
            
        Returns:
            Grade scale dictionary or None
        """
        result = self._supabase.table("grade_scale")\
            .select("*")\
            .eq("grade_letter", grade_letter.upper())\
            .execute()
        
        return result.data[0] if result.data else None
    
    async def get_grade_points(self, grade_letter: str) -> float:
        """
        Get grade points for a letter.
        
        Args:
            grade_letter: Grade letter
            
        Returns:
            Grade points (0.0-4.0), defaults to 0.0 if not found
        """
        grade = await self.get_by_letter(grade_letter)
        return float(grade["points"]) if grade else 0.0
    
    async def does_affect_gpa(self, grade_letter: str) -> bool:
        """
        Check if a grade affects GPA calculation.
        
        Args:
            grade_letter: Grade letter
            
        Returns:
            True if affects GPA, False otherwise
        """
        grade = await self.get_by_letter(grade_letter)
        return grade["affects_gpa"] if grade else True
    
    async def is_passing(self, grade_letter: str) -> bool:
        """
        Check if a grade is considered passing.
        
        Args:
            grade_letter: Grade letter
            
        Returns:
            True if passing, False otherwise
        """
        grade = await self.get_by_letter(grade_letter)
        return grade["is_passing"] if grade else False
    
    async def update(self, grade_letter: str, update_data: GradeScaleUpdate) -> Dict:
        """
        Update a grade scale entry.
        
        Args:
            grade_letter: Grade letter (primary key)
            update_data: Fields to update
            
        Returns:
            Updated grade scale dictionary
            
        Raises:
            NotFoundError: If grade letter not found
        """
        # Check if exists
        existing = await self.get_by_letter(grade_letter)
        if not existing:
            raise NotFoundError("GradeScale", grade_letter)
        
        # Prepare update (exclude None values)
        data = {k: v for k, v in update_data.model_dump().items() if v is not None}
        
        if not data:
            return existing
        
        result = self._supabase.table("grade_scale")\
            .update(data)\
            .eq("grade_letter", grade_letter.upper())\
            .execute()
        
        if not result.data:
            raise Exception("Failed to update grade scale entry")
        
        # Invalidate cache
        self._cache = None
        self._cache_timestamp = None
        
        logger.info(f"Updated grade scale entry: {grade_letter}")
        return result.data[0]
    
    async def get_cached_all(self) -> List[Dict]:
        """
        Get all grade scale entries with caching.
        
        Returns:
            List of grade scale dictionaries
        """
        # Cache for 5 minutes
        if self._cache is not None and self._cache_timestamp is not None:
            if time.time() - self._cache_timestamp < 300:
                return self._cache
        
        self._cache = await self.get_all()
        self._cache_timestamp = time.time()
        
        return self._cache