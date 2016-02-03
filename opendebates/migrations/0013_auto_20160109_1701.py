# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('opendebates', '0012_auto_20151227_1431'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='voter',
            name='first_name',
        ),
        migrations.RemoveField(
            model_name='voter',
            name='last_name',
        ),
        migrations.AddField(
            model_name='submission',
            name='source',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='vote',
            name='source',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
    ]
