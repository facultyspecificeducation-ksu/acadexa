// Responsibility:
// Exposes window.acadexa.updates.* (checkForUpdates, onStatus) by wrapping ipcRenderer.invoke/on calls to channels defined in shared/ipc-channels.ts.
//
// Layer: Electron Preload - API Surface
//
// Communication:
// Consumed by apps/web shared/lib/electronBridge.ts. Forwards requests to main/ipc/handlers/update-handler.ts.

export {};

