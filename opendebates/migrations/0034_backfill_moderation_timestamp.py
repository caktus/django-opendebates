# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def backfill_moderated(apps, schema_editor):
    Submission = apps.get_model('opendebates', 'Submission')
    qs = Submission.objects.filter(
        moderated_at__isnull=True
    ).filter(
        models.Q(approved=False) | models.Q(duplicate_of__isnull=False)
    ).annotate(last_vote=models.Max('vote__created_at'))
    for s in qs:
        s.moderated_at = s.last_vote
        s.save()

    # Deal with merged Submissions whose Votes have been moved
    qs = Submission.objects.filter(
        moderated_at__isnull=True
    ).filter(
        duplicate_of__isnull=False
    ).annotate(last_vote=models.Max('votes_merged_elsewhere__created_at'))
    for s in qs:
        s.moderated_at = s.last_vote
        s.save()

    # Deal with the stragglers
    qs = Submission.objects.filter(moderated_at__isnull=True)
    for s in qs:
        s.moderated_at = s.created_at
        s.save()


class Migration(migrations.Migration):

    dependencies = [
        ('opendebates', '0033_add_moderation_timestamp'),
    ]

    operations = [
        migrations.RunPython(backfill_moderated, reverse_code=migrations.RunPython.noop),
    ]
