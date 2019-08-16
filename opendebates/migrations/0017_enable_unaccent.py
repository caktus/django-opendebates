# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.management import call_command
from django.db import migrations, models


def update_search_index(apps, schema):
    print("Updating search field...")
    call_command("update_search_field", "opendebates")
    print("Updating search field...done")


def no_op(apps, schema):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('opendebates', '0016_auto_20160212_1940'),
    ]

    operations = [
        migrations.RunSQL(
            """
            CREATE EXTENSION IF NOT EXISTS unaccent;
            -- ALTER FUNCTION unaccent(text) IMMUTABLE;
            -- The next line doesn't work:
            -- CREATE INDEX opendebates_submission_search_idx ON opendebates_submission USING gin(to_tsvector('english', search_index));
            """,

            """
            DROP EXTENSION IF EXISTS unaccent;
            DROP INDEX IF EXISTS opendebates_submission_search_idx;
            """
        ),
        migrations.RunPython(
            update_search_index,
            no_op
        )
    ]
