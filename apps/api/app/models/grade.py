# Module: Backend - Models
# Responsibility:
# SQLAlchemy model for the grades table: student_id, course_id, semester_id, grade, grade_points, attempt_no.
#
# Interaction:
# Populated by data_processing/importer/import_service.py from parsed Excel rows. Read by services/gpa_service.py and expert_system/facts/fact_builder.py.


