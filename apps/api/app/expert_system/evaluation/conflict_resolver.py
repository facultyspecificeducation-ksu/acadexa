# Expert System Layer
# This file belongs to the Expert System engine.
#
# Responsibility:
# Orders fired rules by priority and removes mutually-exclusive/duplicate recommendations (e.g. conflicting GPA-band rules) before action execution.
#
# Interaction with rules / facts / recommendations:
# Consumes the list of fired rules from rule_matcher.py and produces the final ordered list passed to actions/action_executor.py.


