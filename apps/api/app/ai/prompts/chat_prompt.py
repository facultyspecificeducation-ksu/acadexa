# AI Assistant Layer
# AI only explains and summarizes existing Expert System output.
# AI does NOT make academic decisions and does NOT modify rules,
# recommendations, or academic records.
#
# Responsibility:
# System prompt for the chat assistant: explicitly scopes the assistant to explaining/summarizing the current student's expert-system recommendations and academic data, and instructs it to never assert new academic decisions.
#
# Interaction:
# Used by ai/services/chat_service.py together with ai/context/context_builder.py and enforced by ai/guardrails/scope_guard.py.


