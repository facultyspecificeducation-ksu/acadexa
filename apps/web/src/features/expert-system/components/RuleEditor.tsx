// Responsibility:
// Admin/Developer UI for building Expert System rules: condition groups (field/operator/value), actions, priority and explanation template.
//
// Layer: Renderer - Feature: expert-system / Components
//
// Communication:
// Saves via hooks/useRules.ts to FastAPI apps/api/app/api/v1/endpoints/rules.py (CRUD for the rules table). Produces the conditions/actions JSON consumed by the inference engine.

export {};

