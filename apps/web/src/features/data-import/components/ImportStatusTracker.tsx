// Responsibility:
// Polls and displays the status of a long-running import job (pending/processing/done/failed) with progress summary.
//
// Layer: Renderer - Feature: data-import / Components
//
// Communication:
// Polls hooks/useDataImport.ts, which reads apps/api import_jobs status via data_processing.jobs.import_job_tracker.

export {};

