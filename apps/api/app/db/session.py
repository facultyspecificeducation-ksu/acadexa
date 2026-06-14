# Module: Backend - Database
# Responsibility:
# Creates the SQLAlchemy engine and session factory pointed at Supabase Postgres using the connection string from core/config.py.
#
# Interaction:
# get_db() from this module is exposed via core/dependencies.py and used by every repository in repositories/*.


