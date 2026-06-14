# Expert System Layer
# This file belongs to the Expert System engine.
#
# Responsibility:
# Executes the Action of each fired rule: CREATE_RECOMMENDATION persists a Recommendation row, TRIGGER_NOTIFICATION calls notification_service, FLAG_PREREQUISITE_VIOLATION marks course-load issues.
#
# Interaction with rules / facts / recommendations:
# Writes via repositories/recommendation_repository.py and calls services/notification_service.py. Uses explanation/explanation_builder.py to attach explanation data to each created recommendation.


