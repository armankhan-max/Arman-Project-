#!/bin/sh
# Starts the app. If no database URL is given, runs a PostgreSQL inside the container (data lives in $FDA_PG_DIR).
set -e
if [ -z "$FDA_DATABASE_URL" ]; then
  PGDIR="${FDA_PG_DIR:-/data/pg}"
  PGBIN=$(ls -d /usr/lib/postgresql/*/bin | tail -1)
  mkdir -p "$PGDIR" /tmp/pgsock && chown -R postgres "$PGDIR" /tmp/pgsock
  if [ ! -f "$PGDIR/PG_VERSION" ]; then su postgres -c "$PGBIN/initdb -D $PGDIR -A trust -U postgres" >/dev/null; fi
  su postgres -c "$PGBIN/pg_ctl -D $PGDIR -l $PGDIR/log.txt -o '-k /tmp/pgsock -c listen_addresses=' -w start"
  su postgres -c "psql -h /tmp/pgsock -U postgres -tc \"select 1 from pg_database where datname='fda'\"" | grep -q 1 || su postgres -c "createdb -h /tmp/pgsock -U postgres fda"
  export FDA_DATABASE_URL="postgresql+psycopg://postgres@/fda?host=/tmp/pgsock"
  echo "Using the built-in database at $PGDIR (set FDA_DATABASE_URL to use an external one)."
fi
alembic upgrade head
exec uvicorn fda.main:app --host 0.0.0.0 --port "${PORT:-8000}"
