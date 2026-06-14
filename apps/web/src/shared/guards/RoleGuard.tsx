// Responsibility:
// Wraps routes/components and renders children only if the current user's role (from features/auth/store via hooks/useSession.ts) is permitted; otherwise redirects or hides the element.
//
// Layer: Renderer - Shared / Guards (RBAC)
//
// Communication:
// Used by app/AppRouter.tsx for route-level RBAC, and inline for component-level RBAC (e.g. hiding admin actions from Academic Advisors). Backend re-enforces RBAC for defense in depth.

export {};

