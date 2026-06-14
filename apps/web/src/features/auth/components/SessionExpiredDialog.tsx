// Responsibility:
// Modal shown when the user's session has expired, prompting re-login.
//
// Layer: Renderer - Feature: auth / Components
//
// Communication:
// Triggered by shared/lib/apiClient.ts response interceptor on 401 responses; redirects to AuthLayout via AppRouter.

export {};

