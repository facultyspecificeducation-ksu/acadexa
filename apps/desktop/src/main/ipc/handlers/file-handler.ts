// Responsibility:
// Handles file system operations: open dialog for selecting Excel transcript files, save dialog for exported reports, and reading file buffers for upload.
//
// Layer: Electron Main Process - IPC Handler
//
// Communication:
// Registered in ipc/ipc-registry.ts on channels from shared/ipc-channels.ts. Invoked from the renderer via window.acadexa.files.* (preload/api/fileApi.ts).

export {};

