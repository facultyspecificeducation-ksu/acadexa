# Data Processing Module
# This module handles Excel ingestion.
# It connects parser output to database models.
#
# Responsibility:
# Updates the import_jobs table status (pending/processing/done/failed) and summary as an import progresses, for UI polling.
#
# Interaction:
# Used by data_processing/importer/import_service.py; read by api/v1/endpoints/data_import.py for the status endpoint polled by apps/web ImportStatusTracker.tsx.


