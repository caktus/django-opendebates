# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('opendebates', '0030_auto_20160927_1242'),
    ]

    operations = [
        migrations.AlterField(
            model_name='voter',
            name='source',
            field=models.CharField(max_length=4096, null=True, blank=True),
        ),
    ]
