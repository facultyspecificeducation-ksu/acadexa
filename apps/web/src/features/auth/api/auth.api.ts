// Responsibility:
// Typed REST calls for authentication: login(credentials) -> SessionUser, logout(), getCurrentUser().
//
// Layer: Renderer - Feature: auth / API Client
//
// Communication:
// Uses shared/lib/apiClient.ts to call FastAPI endpoints apps/api/app/api/v1/endpoints/auth.py. DTOs come from @acadexa/shared-types/auth.types.ts.

export {};

