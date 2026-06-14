# AI Assistant Layer
# AI only explains and summarizes existing Expert System output.
# AI does NOT make academic decisions and does NOT modify rules,
# recommendations, or academic records.
#
# Responsibility:
# chat(messages, context) -> assistant reply. Calls the LLM via ai/client.py with prompts/chat_prompt.py and context from ai/context/context_builder.py, then passes the reply through ai/guardrails/scope_guard.py.
#
# Interaction:
# Called by api/v1/endpoints/ai_assistant.py. The chat assistant explains expert_system recommendations and summarizes academic reports - it does not replace the rule engine or decision logic.


