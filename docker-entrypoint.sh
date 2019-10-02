#!/bin/sh
set -e

wait_time=3
max_waits=10

count=0
until psql $DATABASE_URL -c '\l' >/dev/null 2>&1; do
    count=`expr $count + 1`
    if [ $count -ge $max_waits ] ; then
      >&2 echo "Giving up on Postgres, could not reach at $DATABASE_URL"
      exit 1
    fi
    >&2 echo "Postgres is unavailable at $DATABASE_URL - sleeping ($count)"
    sleep $wait_time
done

>&2 echo "Postgres is up at $DATABASE_URL - continuing"

exec "$@"
