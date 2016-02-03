# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('opendebates', '0006_auto_20150713_2029'),
    ]

    operations = [
        migrations.AddField(
            model_name='submission',
            name='voter',
            field=models.ForeignKey(to='opendebates.Voter', null=True),
        ),
    ]
