// Responsibility:
// Provides the authenticated session context, hydrating it from features/auth/store/auth.store.ts and exposing the current user/role to the component tree.
//
// Layer: Renderer - App Shell / Providers
//
// Communication:
// Wraps App.tsx. Consumed by shared/guards/RoleGuard.tsx and any component needing the current user/role.

export {};

