# Expert System Layer
# This file belongs to the Expert System engine.
#
# Responsibility:
# Defines the registry of supported condition operators (==, !=, >, <, >=, <=, in, between, contains) as a dict mapping operator strings to evaluation functions.
#
# Interaction with rules / facts / recommendations:
# Used by evaluation/condition_evaluator.py to evaluate each Condition against the StudentFactSheet. Extensible without modifying the evaluator itself.


