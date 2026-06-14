// Responsibility:
// React Query hook fetching and marking-as-read in-app notifications; also listens for desktop notification events via electronBridge.notify.*.
//
// Layer: Renderer - Feature: notifications / Hooks
//
// Communication:
// Used by NotificationCenter.tsx. Calls FastAPI apps/api/app/api/v1/endpoints/notifications.py and apps/desktop notification-handler for native OS notifications.

export {};

