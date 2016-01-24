#!/usr/bin/env bash
set -e

find . -name '*.pyc' -delete
flake8 .
coverage erase
coverage run manage.py test --keepdb "$@"
coverage report -m --fail-under 70  # FIXME: increase minimum requirement to 80 ASAP
