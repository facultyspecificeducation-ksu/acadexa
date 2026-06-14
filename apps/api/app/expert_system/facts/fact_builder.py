# Expert System Layer
# This file belongs to the Expert System engine.
#
# Responsibility:
# Builds a StudentFactSheet (GPA, completed credit hours, current semester, grades per course, program requirements, attempted prerequisites, current academic load) for a given student id.
#
# Interaction with rules / facts / recommendations:
# Reads via repositories/student_repository.py and repositories/course_repository.py, and via services/gpa_service.py and services/graduation_service.py for derived values. Output is the engine's working memory, consumed by evaluation/condition_evaluator.py.


