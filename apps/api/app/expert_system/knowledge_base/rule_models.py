# Expert System Layer
# This file belongs to the Expert System engine.
#
# Responsibility:
# Defines internal dataclasses Rule, Condition and Action used by the engine, independent of the Pydantic/SQLAlchemy schema representations.
#
# Interaction with rules / facts / recommendations:
# Produced by knowledge_base/loader.py from raw rule JSON; consumed by evaluation/condition_evaluator.py, evaluation/rule_matcher.py and actions/action_executor.py.


