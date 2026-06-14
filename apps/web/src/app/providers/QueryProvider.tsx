// Responsibility:
// Provides the React Query client used by all feature 'hooks' modules for data fetching/caching against the FastAPI backend.
//
// Layer: Renderer - App Shell / Providers
//
// Communication:
// Wraps App.tsx. The underlying HTTP client is shared/lib/apiClient.ts, configured with the backend base URL from Electron's api-config.service.

export {};

