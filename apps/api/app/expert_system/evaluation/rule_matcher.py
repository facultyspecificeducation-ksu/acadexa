# Expert System Layer
# This file belongs to the Expert System engine.
#
# Responsibility:
# Iterates all loaded rules and, for each, evaluates all of its conditions via condition_evaluator.py; rules where all conditions are true are marked as 'fired'.
#
# Interaction with rules / facts / recommendations:
# Consumes Rule objects from knowledge_base/loader.py and facts from facts/fact_builder.py. Produces a list of fired rules passed to evaluation/conflict_resolver.py.


