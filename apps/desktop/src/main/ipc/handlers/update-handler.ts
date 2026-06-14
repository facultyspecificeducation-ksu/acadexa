// Responsibility:
// Handles application auto-update IPC requests (check/download/install) by delegating to services/update.service.ts and forwarding status events.
//
// Layer: Electron Main Process - IPC Handler
//
// Communication:
// Registered in ipc/ipc-registry.ts. Invoked from the renderer via window.acadexa.updates.* (preload/api/updateApi.ts).

export {};

