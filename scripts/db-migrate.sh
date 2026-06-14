#!/usr/bin/env bash
# Runs Alembic migrations for apps/api against the target environment
# (local Postgres in docker-compose, or a remote Supabase project).
echo "Running: alembic upgrade head (apps/api)"

