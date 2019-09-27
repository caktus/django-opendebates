# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2019-09-27 12:56
from __future__ import unicode_literals

from django.contrib.postgres.search import SearchVector, SearchQuery
from django.db import migrations


search_vectors = SearchVector('idea', weight='A') + SearchVector('keywords', weight='A')
def populate_submission_search_vector(apps, schema_editor):
    Submission = apps.get_model('opendebates', 'Submission')
    Submission.objects.update(search_vector=search_vectors)


class Migration(migrations.Migration):

    dependencies = [
        ('opendebates', '0042_submission_search_vector_and_index'),
    ]

    operations = [
        migrations.RunPython(populate_submission_search_vector, reverse_code=migrations.RunPython.noop),
    ]
