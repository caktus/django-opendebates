# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('opendebates', '0005_auto_20150514_2037'),
    ]

    operations = [
        migrations.AddField(
            model_name='voter',
            name='first_name',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='voter',
            name='last_name',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
    ]
