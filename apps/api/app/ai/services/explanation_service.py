# AI Assistant Layer
# AI only explains and summarizes existing Expert System output.
# AI does NOT make academic decisions and does NOT modify rules,
# recommendations, or academic records.
#
# Responsibility:
# explain(recommendation) -> natural language text. Calls the LLM via ai/client.py with prompts/explanation_prompt.py to rephrase an existing expert_system explanation conversationally.
#
# Interaction:
# Called by api/v1/endpoints/recommendations.py or ai_assistant.py after expert_system/runner.run_evaluation() has already produced the recommendation. Read-only with respect to expert_system output.


