# AI Assistant Layer
# AI only explains and summarizes existing Expert System output.
# AI does NOT make academic decisions and does NOT modify rules,
# recommendations, or academic records.
#
# Responsibility:
# Post-processes AI responses to detect and strip/flag any attempt by the model to assert new rules, recommendations, or academic decisions not present in the expert_system output.
#
# Interaction:
# Used by ai/services/chat_service.py and explanation_service.py as the final step before returning a response to api/v1/endpoints/ai_assistant.py / recommendations.py.


