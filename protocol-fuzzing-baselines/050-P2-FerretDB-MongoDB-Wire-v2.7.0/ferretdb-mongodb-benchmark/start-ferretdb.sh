#!/usr/bin/env bash
set -euo pipefail

: "${POSTGRES_HOST:=documentdb}"
: "${POSTGRES_PORT:=5432}"
: "${POSTGRES_USER:=benchmark}"
: "${POSTGRES_PASSWORD:=benchmark}"
export PGPASSWORD=${POSTGRES_PASSWORD}
# FerretDB v2.7.0's matched DocumentDB extension is initialized in PostgreSQL's
# `postgres` database; pg_cron requires that database for extension jobs. Keep
# the extension intact and remove every MongoDB database's collections through
# DocumentDB's supported drop_database API before launching the next testcase.
psql -v ON_ERROR_STOP=1 -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" \
  -U "${POSTGRES_USER}" -d postgres <<'SQL'
DO $reset$
DECLARE
  mongo_database text;
BEGIN
  FOR mongo_database IN
    SELECT DISTINCT database_name FROM documentdb_api_catalog.collections
  LOOP
    PERFORM documentdb_api.drop_database(mongo_database, NULL::documentdb_core.bson);
  END LOOP;
END;
$reset$;
SQL

export FERRETDB_POSTGRESQL_URL="postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/postgres?sslmode=disable"
export FERRETDB_LISTEN_ADDR="127.0.0.1:27017"
export FERRETDB_AUTH=false
exec /usr/local/bin/ferretdb
