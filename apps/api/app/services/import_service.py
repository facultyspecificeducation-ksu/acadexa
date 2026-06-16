"""
================================================================================
Import Service for Acadexa API
================================================================================

Business logic for Excel import pipeline:
- Upload Excel files to Supabase Storage
- Create import jobs
- Parse Excel files using ExcelParser
- Track import progress and errors
- Retrieve import history

Security: Uses service role client for background parsing (bypasses RLS).
Import jobs are created with authenticated client but parsing uses service role.

Author: Acadexa Team
Version: 1.2.0
================================================================================
"""

import asyncio
import hashlib
import logging
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID

from supabase import Client

from app.core.exceptions import NotFoundError, ConflictError, BusinessRuleError
from app.core.supabase import get_service_role_client

logger = logging.getLogger("acadexa.services.import_service")

# Import ExcelParser
try:
    from app.utils.excel_parser import ExcelParser
except ImportError:
    logger.warning("ExcelParser not found. Import will fail.")
    ExcelParser = None


class ImportService:
    """Service for Excel import pipeline."""
    
    def __init__(self, supabase_client: Optional[Client] = None):
        """
        Initialize ImportService.
        
        Args:
            supabase_client: Optional authenticated client for job creation.
                           If not provided, service role client is used.
        """
        self._auth_client = supabase_client
        self._service_client = get_service_role_client()
        self._background_tasks = set()  # Track running tasks
    
    def _get_client(self, use_auth: bool = True) -> Client:
        """Get appropriate client based on context."""
        if use_auth and self._auth_client:
            return self._auth_client
        return self._service_client
    
    async def create_import_job(
        self,
        department_id: UUID,
        file_name: str,
        file_url: str,
        uploaded_by: UUID,
    ) -> Dict:
        """
        Create an import job record.
        
        Args:
            department_id: Department UUID
            file_name: Original file name
            file_url: Storage URL of uploaded file
            uploaded_by: User ID who uploaded
            
        Returns:
            Created import job dictionary
        """
        client = self._get_client(use_auth=True)
        
        job_data = {
            "department_id": str(department_id),
            "file_name": file_name,
            "file_url": file_url,
            "uploaded_by": str(uploaded_by),
            "status": "pending",
            "total_students": 0,
            "successful_records": 0,
            "failed_records": 0,
            "error_log": [],
        }
        
        result = client.table("import_jobs")\
            .insert(job_data)\
            .execute()
        
        if not result.data:
            raise Exception("Failed to create import job")
        
        logger.info(f"Created import job {result.data[0]['id']} for department {department_id}")
        return result.data[0]
    
    async def get_import_job(self, job_id: UUID) -> Dict:
        """
        Get an import job by ID.
        
        Args:
            job_id: Job UUID
            
        Returns:
            Import job dictionary
        """
        client = self._get_client(use_auth=True)
        
        result = client.table("import_jobs")\
            .select("*, departments(name_ar), profiles(full_name)")\
            .eq("id", str(job_id))\
            .execute()
        
        if not result.data:
            raise NotFoundError("ImportJob", str(job_id))
        
        job = result.data[0]
        
        # Get linked files
        files_result = client.table("imported_files")\
            .select("*")\
            .eq("import_job_id", str(job_id))\
            .execute()
        
        job["imported_files"] = files_result.data or []
        
        # Add department name
        if job.get("departments"):
            job["department_name_ar"] = job["departments"].get("name_ar")
        
        # Add uploader name
        if job.get("profiles"):
            job["uploaded_by_name"] = job["profiles"].get("full_name")
        
        return job
    
    async def get_import_jobs(
        self,
        department_id: Optional[UUID] = None,
        status: Optional[str] = None,
        uploaded_by: Optional[UUID] = None,
        page: int = 1,
        limit: int = 50,
    ) -> Tuple[List[Dict], int]:
        """
        Get paginated list of import jobs.
        
        Args:
            department_id: Filter by department
            status: Filter by status (pending, processing, completed, failed)
            uploaded_by: Filter by uploader
            page: Page number
            limit: Items per page
            
        Returns:
            Tuple of (jobs list, total count)
        """
        client = self._get_client(use_auth=True)
        
        if limit > 100:
            limit = 100
        
        offset = (page - 1) * limit
        
        query = client.table("import_jobs")\
            .select("*, departments(name_ar), profiles(full_name)", count="exact")\
            .order("created_at", desc=True)
        
        if department_id:
            query = query.eq("department_id", str(department_id))
        
        if status:
            query = query.eq("status", status)
        
        if uploaded_by:
            query = query.eq("uploaded_by", str(uploaded_by))
        
        query = query.range(offset, offset + limit - 1)
        
        result = query.execute()
        
        jobs = result.data or []
        total = result.count or 0
        
        # Add department names and uploader names
        for job in jobs:
            if job.get("departments"):
                job["department_name_ar"] = job["departments"].get("name_ar")
            if job.get("profiles"):
                job["uploaded_by_name"] = job["profiles"].get("full_name")
        
        return jobs, total
    
    async def get_import_job_status(self, job_id: UUID) -> Dict:
        """
        Get import job status for polling.
        
        Args:
            job_id: Job UUID
            
        Returns:
            Status dictionary
        """
        client = self._get_client(use_auth=True)
        
        result = client.table("import_jobs")\
            .select("id, status, total_students, successful_records, failed_records, completed_at, error_log")\
            .eq("id", str(job_id))\
            .execute()
        
        if not result.data:
            raise NotFoundError("ImportJob", str(job_id))
        
        job = result.data[0]
        
        return {
            "job_id": job["id"],
            "status": job["status"],
            "total_students": job.get("total_students", 0),
            "successful_records": job.get("successful_records", 0),
            "failed_records": job.get("failed_records", 0),
            "completed_at": job.get("completed_at"),
            "has_errors": job.get("failed_records", 0) > 0,
        }
    
    async def update_import_job_status(
        self,
        job_id: UUID,
        status: str,
        total_students: Optional[int] = None,
        successful_records: Optional[int] = None,
        failed_records: Optional[int] = None,
        error_log: Optional[List[Dict]] = None,
        completed_at: Optional[str] = None,
    ) -> Dict:
        """
        Update import job status (internal use).
        
        Args:
            job_id: Job UUID
            status: New status
            total_students: Total students in file
            successful_records: Successfully parsed records
            failed_records: Failed records
            error_log: Error log entries
            completed_at: Completion timestamp
            
        Returns:
            Updated job dictionary
        """
        client = self._get_client(use_auth=False)  # Use service role for updates
        
        update_data = {"status": status}
        
        if total_students is not None:
            update_data["total_students"] = total_students
        
        if successful_records is not None:
            update_data["successful_records"] = successful_records
        
        if failed_records is not None:
            update_data["failed_records"] = failed_records
        
        if error_log is not None:
            update_data["error_log"] = error_log
        
        if completed_at is not None:
            update_data["completed_at"] = completed_at
        elif status in ["completed", "failed"]:
            update_data["completed_at"] = datetime.now(timezone.utc).isoformat()
        
        result = client.table("import_jobs")\
            .update(update_data)\
            .eq("id", str(job_id))\
            .execute()
        
        if not result.data:
            raise Exception(f"Failed to update job {job_id}")
        
        logger.info(f"Updated job {job_id} status to {status}")
        return result.data[0]
    
    async def cancel_import_job(self, job_id: UUID, user_id: UUID, is_admin: bool) -> Dict:
        """
        Cancel a pending import job.
        
        Args:
            job_id: Job UUID
            user_id: User attempting cancellation
            is_admin: Whether user is admin
            
        Returns:
            Updated job dictionary
        """
        client = self._get_client(use_auth=True)
        
        # Get job to check permissions
        job = await self.get_import_job(job_id)
        
        # Check permissions
        if not is_admin and str(job["uploaded_by"]) != str(user_id):
            raise BusinessRuleError("Only the uploader or admin can cancel this job", "PERMISSION_DENIED")
        
        # Only pending jobs can be cancelled
        if job["status"] != "pending":
            raise BusinessRuleError(f"Cannot cancel job with status {job['status']}", "INVALID_STATUS")
        
        return await self.update_import_job_status(job_id, "failed")
    
    async def delete_import_job(self, job_id: UUID) -> bool:
        """
        Delete an import job (admin only).
        
        Args:
            job_id: Job UUID
            
        Returns:
            True if deleted
        """
        client = self._get_client(use_auth=False)  # Service role for deletion
        
        # Check if exists
        await self.get_import_job(job_id)
        
        # Delete the job (cascades to imported_files, raw_students, raw_courses)
        result = client.table("import_jobs")\
            .delete()\
            .eq("id", str(job_id))\
            .execute()
        
        deleted = len(result.data) > 0
        if deleted:
            logger.info(f"Deleted import job {job_id}")
        
        return deleted
    
    async def upload_and_parse(
        self,
        department_id: UUID,
        file_content: bytes,
        file_name: str,
        uploaded_by: UUID,
        department_code: Optional[str] = None,
    ) -> Dict:
        """
        Upload Excel file to storage and start parsing.
        
        This is the main entry point for the import workflow.
        
        Args:
            department_id: Department UUID
            file_content: Binary content of Excel file
            file_name: Original file name
            uploaded_by: User ID uploading
            department_code: Department code for parser (optional)
            
        Returns:
            Import job dictionary
        """
        # Get department code if not provided
        if not department_code:
            client = self._get_client(use_auth=True)
            dept_result = client.table("departments")\
                .select("code")\
                .eq("id", str(department_id))\
                .execute()
            
            if dept_result.data:
                department_code = dept_result.data[0]["code"]
            else:
                raise NotFoundError("Department", str(department_id))
        
        # Generate storage path
        job_id = str(uuid.uuid4())
        storage_path = f"imports/{job_id}/{file_name}"
        
        # Upload to Supabase Storage
        try:
            from app.core.supabase import get_supabase_manager
            manager = get_supabase_manager()
            storage_client = manager.get_service_role_client()
            
            # Upload file
            storage_client.storage.from_("imports").upload(
                storage_path,
                file_content,
                {"content-type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}
            )
            
            # Use signed URL for private bucket
            file_url = storage_client.storage.from_("imports").create_signed_url(storage_path, 3600)
            
        except Exception as e:
            logger.error(f"Failed to upload file to storage: {e}")
            raise Exception(f"Storage upload failed: {str(e)}")
        
        # Create import job record
        job = await self.create_import_job(
            department_id=department_id,
            file_name=file_name,
            file_url=file_url,
            uploaded_by=uploaded_by,
        )
        
        actual_job_id = job["id"]
        
        # Create imported_files record
        client = self._get_client(use_auth=True)
        client.table("imported_files").insert({
            "import_job_id": str(actual_job_id),
            "original_name": file_name,
            "storage_path": storage_path,
            "hash": hashlib.md5(file_content).hexdigest(),
        }).execute()
        
        # Start parsing in background using asyncio.create_task
        # This prevents blocking the event loop
        task = asyncio.create_task(
            self._parse_and_save(actual_job_id, file_content, department_code)
        )
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
        
        logger.info(f"Import job {actual_job_id} started in background")
        
        return job
    
    def _background_tasks_discard(self, task):
        """Remove completed task from tracking set."""
        self._background_tasks.discard(task)
    
    async def _parse_and_save(self, job_id: UUID, file_content: bytes, department_code: str) -> None:
        """
        Parse Excel file and save data to database.
        
        Runs in background as a separate async task.
        
        Args:
            job_id: Import job UUID
            file_content: Binary content of Excel file
            department_code: Department code for parser
        """
        try:
            # Update status to processing
            await self.update_import_job_status(job_id, "processing")
            
            # Save file to temp location for ExcelParser
            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
                tmp_file.write(file_content)
                tmp_path = Path(tmp_file.name)
            
            try:
                # Parse using ExcelParser (CPU-bound - runs in thread pool via asyncio.to_thread)
                if ExcelParser is None:
                    raise Exception("ExcelParser not available")
                
                # Run parser in thread pool to avoid blocking the event loop
                parser = await asyncio.to_thread(
                    self._parse_excel_sync,
                    tmp_path,
                    department_code
                )
                
                students, errors = parser.parse_all_students()
                stats = parser.get_stats()
                
                # Update job with results
                await self.update_import_job_status(
                    job_id=job_id,
                    status="completed" if len(errors) == 0 else "completed",
                    total_students=stats.get("students", 0),
                    successful_records=len(students),
                    failed_records=len(errors),
                    error_log=errors if errors else None,
                )
                
                logger.info(f"Import job {job_id} completed: {len(students)} students, {len(errors)} errors")
                
            finally:
                # Clean up temp file
                tmp_path.unlink(missing_ok=True)
                
        except Exception as e:
            logger.error(f"Import job {job_id} failed: {e}")
            await self.update_import_job_status(
                job_id=job_id,
                status="failed",
                error_log=[{"error": str(e)}],
            )
    
    def _parse_excel_sync(self, tmp_path: Path, department_code: str):
        """Synchronous wrapper for ExcelParser (runs in thread pool)."""
        return ExcelParser(tmp_path, department_code=department_code)
    
    async def get_students_by_import_job(self, job_id: UUID) -> List[Dict]:
        """
        Get students imported from a specific job.
        
        Args:
            job_id: Import job UUID
            
        Returns:
            List of student dictionaries
        """
        client = self._get_client(use_auth=True)
        
        result = client.table("students")\
            .select("id, student_code, name, department_id, curriculum_id, enrollment_year, cumulative_gpa")\
            .eq("last_import_job_id", str(job_id))\
            .execute()
        
        return result.data or []
    
    async def get_import_job_file_url(self, job_id: UUID, file_id: UUID) -> str:
        """
        Get signed URL for downloading original file.
        
        Args:
            job_id: Import job UUID
            file_id: Imported file UUID
            
        Returns:
            Signed download URL (valid for 1 hour)
        """
        client = self._get_client(use_auth=True)
        
        # Verify file belongs to job
        result = client.table("imported_files")\
            .select("storage_path")\
            .eq("id", str(file_id))\
            .eq("import_job_id", str(job_id))\
            .execute()
        
        if not result.data:
            raise NotFoundError("ImportedFile", str(file_id))
        
        storage_path = result.data[0]["storage_path"]
        
        # Generate signed URL (valid for 1 hour)
        from app.core.supabase import get_supabase_manager
        manager = get_supabase_manager()
        storage_client = manager.get_service_role_client()
        
        file_url = storage_client.storage.from_("imports").create_signed_url(storage_path, 3600)
        
        return file_url