// Responsibility:
// React Query mutation hook that calls api/auth.api.ts login(), stores the session in store/auth.store.ts, and handles error states.
//
// Layer: Renderer - Feature: auth / Hooks
//
// Communication:
// Used by components/LoginForm.tsx. Calls api/auth.api.ts which talks to FastAPI POST /api/v1/auth/login.

export {};

