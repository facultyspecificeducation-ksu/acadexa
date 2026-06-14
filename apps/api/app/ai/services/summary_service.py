# AI Assistant Layer
# AI only explains and summarizes existing Expert System output.
# AI does NOT make academic decisions and does NOT modify rules,
# recommendations, or academic records.
#
# Responsibility:
# summarize(report_data) -> narrative summary text. Calls the LLM via ai/client.py with prompts/summary_prompt.py to add a narrative paragraph to a report.
#
# Interaction:
# Called by services/report_service.py. Operates only on figures already computed by deterministic services and expert_system.


