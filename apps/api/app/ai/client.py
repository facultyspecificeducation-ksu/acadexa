# AI Assistant Layer
# AI only explains and summarizes existing Expert System output.
# AI does NOT make academic decisions and does NOT modify rules,
# recommendations, or academic records.
#
# Responsibility:
# Thin wrapper around the LLM provider SDK (model name, API key) read from core/config.py, isolating provider-specific details.
#
# Interaction:
# Used by ai/services/explanation_service.py, summary_service.py and chat_service.py as the single LLM call point.


