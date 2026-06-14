# Expert System Layer
# This file belongs to the Expert System engine.
#
# Responsibility:
# Builds the structured explanation object for a fired rule: rule_id, rule_name, reason (template filled with actual fact values), evidence (the exact fact values used), explanation text and priority.
#
# Interaction with rules / facts / recommendations:
# Called by actions/action_executor.py when creating a Recommendation. This is what answers 'Why was this recommendation generated?' and is read-only input for ai/services/explanation_service.py.


