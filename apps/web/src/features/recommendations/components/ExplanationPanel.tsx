// Responsibility:
// Shows the full explanation for a recommendation: applied rule id/name, evidence values used, full explanation text, and an 'Explain in plain language' action.
//
// Layer: Renderer - Feature: recommendations / Components
//
// Communication:
// The plain-language action calls api/recommendations.api.ts -> FastAPI ai_assistant explanation_service, which rephrases (never changes) the explanation.

export {};

