#!/usr/bin/env bash
set -e

find . -name '*.pyc' -delete
flake8 .
coverage run manage.py test --keepdb "$@"
coverage report -m --fail-under 40  # FIXME: increase minimum requirement to 80 ASAP
