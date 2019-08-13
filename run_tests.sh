#!/usr/bin/env bash
set -e

find . -name '*.pyc' -delete

find . -name "*.js" -not \( \
    -path "./static/*" -o \
    -path "*/bower_components/*" -o \
    -path "./node_modules/*" -o \
    -path "*/jquery.cookie.js" \) -print0 | xargs -0 jshint

flake8 .
coverage erase
coverage run manage.py test --keepdb -v 2 "$@"
coverage report -m --fail-under 90
