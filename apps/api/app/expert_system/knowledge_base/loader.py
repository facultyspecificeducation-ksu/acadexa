# Expert System Layer
# This file belongs to the Expert System engine.
#
# Responsibility:
# Loads all rules where is_active = true from the rules table, ordered by priority, and converts each row's JSON conditions/actions into internal dataclasses.
#
# Interaction with rules / facts / recommendations:
# Reads from repositories/rule_repository.py (rules). Produces a list of Rule objects (rule_models.py) consumed by evaluation/rule_matcher.py.


