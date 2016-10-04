# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('opendebates', '0031_add_current_votes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='submission',
            name='current_votes',
            field=models.IntegerField(default=0, db_index=True),
        ),
        migrations.AlterField(
            model_name='topsubmission',
            name='current_votes',
            field=models.IntegerField(default=0),
        ),
    ]
