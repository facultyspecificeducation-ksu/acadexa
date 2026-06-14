// Responsibility:
// Zustand store holding the current session: authenticated user, role (Developer/Admin/Academic Advisor), and auth token/session id.
//
// Layer: Renderer - Feature: auth / State
//
// Communication:
// Written to by hooks/useLogin.ts; read by app/providers/AuthProvider.tsx, shared/guards/RoleGuard.tsx and shared/lib/apiClient.ts (auth header).

export {};

