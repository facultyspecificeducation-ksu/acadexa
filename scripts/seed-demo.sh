#!/usr/bin/env bash
# Seeds demo data for graduation-project demos:
# - demo users for each role (Developer, Admin, Academic Advisor)
# - a starter set of Expert System rules (GPA, warning, graduation, etc.)
# - a small set of demo students/courses/grades.
echo "Running: python -m app.db.seed.seed_data (apps/api)"

