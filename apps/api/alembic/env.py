# Module: Backend - Database / Migrations
# Responsibility:
# Alembic environment configuration: reads the database URL from core/config.py and the metadata from db/base.py + models/* to autogenerate migrations.
#
# Interaction:
# Used by scripts/db-migrate.sh (alembic upgrade head) against local or Supabase Postgres.


