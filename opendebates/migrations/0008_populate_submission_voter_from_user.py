# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def lookup_voter_from_user(apps, schema_editor):
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    Submission = apps.get_model("opendebates", "Submission")
    for submission in Submission.objects.all():
        submission.voter = submission.user.voter
        submission.save()

class Migration(migrations.Migration):

    dependencies = [
        ('opendebates', '0007_submission_voter'),
    ]

    operations = [
        migrations.RunPython(lookup_voter_from_user),
    ]