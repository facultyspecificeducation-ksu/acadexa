# TODO — Phase 3: API Contract Alignment

- [x] Wire new routers for Group 2 (me/roles) and Group 13 (advisor notes) into `apps/api/app/api/v1/router.py`.
- [ ] Implement required route/path fixes:
  - [ ] Health response shape per spec (remove extra keys).
  - [ ] Add dashboard endpoints: `/api/v1/department-statistics`, `/api/v1/department-statistics/snapshot`, `/api/v1/students/at-risk`.
  - [ ] Add export endpoints under `/api/v1/students/.../export` (currently live under `/api/v1/export/...`).
- [ ] Add export endpoint for analysis issues: `/api/v1/students/:student_id/analyses/issues/export`.
- [ ] Route verification (ensure all spec endpoints are reachable with correct methods/paths).
- [ ] Confirm backend boots successfully.
- [ ] Produce spec endpoint status table + final file contents for every changed/created file.

