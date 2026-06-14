// Responsibility:
// Configures the Axios/fetch instance used by all feature 'api' modules: sets base URL (from electronBridge/api-config), attaches the auth token from features/auth/store, and handles global error responses (401 -> SessionExpiredDialog).
//
// Layer: Renderer - Shared / Lib
//
// Communication:
// Imported by every features/*/api/*.ts module. The single point of contact between the renderer and FastAPI apps/api.

export {};

