// Responsibility:
// Typed REST calls for Excel import: uploadExcel(file), getImportStatus(jobId), confirmImport(jobId).
//
// Layer: Renderer - Feature: data-import / API Client
//
// Communication:
// Uses shared/lib/apiClient.ts to call apps/api/app/api/v1/endpoints/data_import.py (multipart upload).

export {};

