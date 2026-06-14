// Responsibility:
// Central registration point for every ipcMain.handle() call. Imports each handler module and wires it to its channel name from shared/ipc-channels.ts.
//
// Layer: Electron Main Process - IPC
//
// Communication:
// Called once from main/index.ts at startup. Single source of truth for the set of channels exposed to the renderer.

export {};

