// Responsibility:
// Handles printing and print-to-PDF of academic/recommendation reports using webContents.print and webContents.printToPDF.
//
// Layer: Electron Main Process - IPC Handler
//
// Communication:
// Registered in ipc/ipc-registry.ts. Invoked from the renderer via window.acadexa.print.* (preload/api/printApi.ts).

export {};

