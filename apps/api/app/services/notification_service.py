# Module: Backend - Services
# Responsibility:
# Creates in-app notification records and (when running under Electron) requests desktop notifications.
#
# Interaction:
# Called by data_processing/importer/import_service.py after imports and by the recommendation evaluation flow after expert_system runs. Writes via models/notification.py.


