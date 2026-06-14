// Responsibility:
// Handles native OS desktop notifications (new recommendations, import completion) using the Electron Notification API.
//
// Layer: Electron Main Process - IPC Handler
//
// Communication:
// Registered in ipc/ipc-registry.ts. Invoked from the renderer via window.acadexa.notify.* (preload/api/notificationApi.ts).

export {};

