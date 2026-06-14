# Module: Backend - Tests / E2E
# Responsibility:
# End-to-end test: uploads a sample Excel transcript (fixtures/sample_transcripts), runs data_processing import, triggers expert_system evaluation, and asserts recommendations and notifications are created.
#
# Interaction:
# Covers data_processing -> expert_system -> services/notification_service -> api/v1/endpoints/recommendations end-to-end.


