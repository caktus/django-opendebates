# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('opendebates', '0034_backfill_moderation_timestamp'),
    ]

    operations = [
        migrations.AddField(
            model_name='vote',
            name='is_invalid',
            field=models.NullBooleanField(),
        ),
        migrations.AddField(
            model_name='vote',
            name='is_suspicious',
            field=models.NullBooleanField(),
        ),
        migrations.AddField(
            model_name='vote',
            name='sessionid',
            field=models.CharField(max_length=40, null=True, blank=True),
        ),
    ]
