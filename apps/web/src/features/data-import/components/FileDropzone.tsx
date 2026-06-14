// Responsibility:
// Drag-and-drop / file-picker UI for selecting Excel transcript files, using electronBridge.files.openExcel() when running inside Electron.
//
// Layer: Renderer - Feature: data-import / Components
//
// Communication:
// On file selection, uploads via hooks/useDataImport.ts to FastAPI apps/api/app/api/v1/endpoints/data_import.py.

export {};

