# Expert System Layer
# This file belongs to the Expert System engine.
#
# Responsibility:
# Validates the structure of a rule's conditions/actions JSON (required fields, known operators, known action types) on create/update.
#
# Interaction with rules / facts / recommendations:
# Called by api/v1/endpoints/rules.py before persisting a rule via rule_repository.py, and by knowledge_base/loader.py defensively when loading rules.


