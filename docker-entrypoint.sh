#!/bin/sh
set -e

until psql $DATABASE_URL -c '\l' >/dev/null 2>&1; do
    >&2 echo "Postgres is unavailable - sleeping"
    sleep 1
done

>&2 echo "Postgres is up - continuing"

exec "$@"
