# AI Assistant Layer
# AI only explains and summarizes existing Expert System output.
# AI does NOT make academic decisions and does NOT modify rules,
# recommendations, or academic records.
#
# Responsibility:
# Gathers the allowed context for AI prompts: the current student's StudentFactSheet (read-only, via expert_system/facts) and their existing recommendations/explanations.
#
# Interaction:
# Used by ai/services/chat_service.py and explanation_service.py to restrict what data the LLM can see - no arbitrary database access.


