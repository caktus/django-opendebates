# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('opendebates', '0013_auto_20160109_1701'),
    ]

    operations = [
        migrations.AlterField(
            model_name='submission',
            name='approved',
            field=models.BooleanField(default=False, db_index=True),
        ),
        migrations.AlterField(
            model_name='submission',
            name='has_duplicates',
            field=models.BooleanField(default=False, db_index=True),
        ),
    ]
