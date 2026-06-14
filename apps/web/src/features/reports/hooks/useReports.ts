// Responsibility:
// React Query hooks: getStudentProgressReport(studentId), getRecommendationReport(studentId), getAcademicAnalysisReport(filters).
//
// Layer: Renderer - Feature: reports / Hooks
//
// Communication:
// Used by ReportViewer.tsx. Calls api/reports.api.ts -> FastAPI apps/api/app/api/v1/endpoints/reports.py, which may include an AI-generated narrative summary.

export {};

