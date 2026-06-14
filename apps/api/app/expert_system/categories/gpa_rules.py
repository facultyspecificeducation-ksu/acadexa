# Expert System Layer
# This file belongs to the Expert System engine.
#
# Responsibility:
# Holds GPA-category helper computations referenced by rule conditions (e.g. derived GPA bands), without hardcoding business outcomes.
#
# Interaction with rules / facts / recommendations:
# Helper functions may be referenced when building facts in facts/fact_builder.py; actual GPA threshold decisions remain in the rules table, not in this file.


