# Expert System Layer
# This file belongs to the Expert System engine.
#
# Responsibility:
# Defines the InferenceEngine class that orchestrates a full evaluation cycle: build facts, load rules, evaluate conditions, resolve conflicts, execute actions, build explanations.
#
# Interaction with rules / facts / recommendations:
# Coordinates knowledge_base/loader.py (rules), facts/fact_builder.py (facts), evaluation/* (matching), actions/action_executor.py (writing recommendations) and explanation/explanation_builder.py (explanations).


