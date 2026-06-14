// Responsibility:
// Resolves the FastAPI backend base URL depending on deployment mode (local bundled sidecar vs remote/cloud-hosted Supabase + FastAPI).
//
// Layer: Electron Main Process - Services
//
// Communication:
// Read by preload/api modules so the renderer's apiClient (apps/web shared/lib/apiClient.ts) knows which backend URL to call.

export {};

