# Expert System Layer
# This file belongs to the Expert System engine.
#
# Responsibility:
# Public entry point of the Expert System: run_evaluation(student_id) builds facts, loads rules, runs evaluation/actions, and returns the list of created Recommendation objects.
#
# Interaction with rules / facts / recommendations:
# Called from services/ (e.g. after data import, or on-demand from api/v1/endpoints/recommendations.py). This is the ONLY function other layers should call to trigger the engine.


