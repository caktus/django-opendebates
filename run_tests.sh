#!/usr/bin/env bash
set -e

find . -name '*.pyc' -delete
flake8 opendebates
cd opendebates
coverage run manage.py test --keepdb "$@"
coverage report -m --fail-under 30  # FIXME: increase minimum requirement to 80 ASAP
