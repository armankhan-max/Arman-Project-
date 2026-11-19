#!/bin/sh
# Starts the app. If no database URL is given, runs a PostgreSQL inside the container (data lives in $FDA_PG_DIR).
# Works as root (Docker, Render) and as an unprivileged user (Hugging Face Spaces run as uid 1000).
set -e
if [ -z "$FDA_DATABASE_URL" ]; then
  PGDIR="${FDA_PG_DIR:-/data/pg}"
  SOCK="${FDA_PG_SOCK:-/tmp/pgsock}"
  PGBIN=$(ls -d /usr/lib/postgresql/*/bin | tail -1)
  mkdir -p "$PGDIR" "$SOCK"
  if [ "$(id -u)" = "0" ]; then
    chown -R postgres "$PGDIR" "$SOCK"
    AS="su postgres -c"
  else
    AS="sh -c"
  fi
  if [ ! -f "$PGDIR/PG_VERSION" ]; then $AS "$PGBIN/initdb -D $PGDIR -A trust -U postgres" >/dev/null; fi
  $AS "$PGBIN/pg_ctl -D $PGDIR -l $PGDIR/log.txt -o '-k $SOCK -c listen_addresses= -c shared_buffers=64MB -c max_connections=40' -w start"
  $AS "$PGBIN/psql -h $SOCK -U postgres -tc \"select 1 from pg_database where datname='fda'\"" | grep -q 1 || $AS "$PGBIN/createdb -h $SOCK -U postgres fda"
  export FDA_DATABASE_URL="postgresql+psycopg://postgres@/fda?host=$SOCK"
  echo "Using the built-in database at $PGDIR (set FDA_DATABASE_URL to use an external one)."
fi
alembic upgrade head
exec uvicorn fda.main:app --host 0.0.0.0 --port "${PORT:-8000}"
