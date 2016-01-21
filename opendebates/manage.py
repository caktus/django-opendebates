#!/usr/bin/env python
import os
import sys

import dotenv

dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".env"))
dotenv.read_dotenv(dotenv_path)

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "opendebates.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
